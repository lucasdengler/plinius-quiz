import streamlit as st
import pandas as pd
import time
import os
import google.generativeai as genai

# ---- 1. DATENBASIS ----
SAETZE = [
    {"satz_id": 1, "latein": "Erat Miseni classemque imperio praesens regebat.", "loesung": "Er war in Misenum und befehligte dort persönlich die Flotte.", "vokabeln": "erat Miseni = er war in Misenum\nclassis, is f = Flotte\nimperio (Abl.) = mit der Befehlsgewalt\npraesens = anwesend / persönlich", "grammatik": "• 'Miseni' ist ein Lokativ (Antwort auf 'Wo?').\n• 'imperio' steht im Ablativus instrumentalis (Wodurch? -> mit Befehlsgewalt).\n• 'praesens' wirkt hier prädikativ, am besten mit 'persönlich' oder 'selbst' übersetzen."},
    {"satz_id": 2, "latein": "Nonum kal. Septembres hora fere septima mater mea indicat ei apparere nubem inusitata et magnitudine et specie.", "loesung": "Am 24. August, etwa gegen ein Uhr mittags, wies meine Mutter ihn darauf hin, dass eine Wolke von ungewöhnlicher Größe und Gestalt auftauchte.", "vokabeln": "nonum kal. Septembres = am 24. August\nhora fere septima = ca. 13 Uhr\nindicat = wies hin / meldete\napparere = erscheinen", "grammatik": "• Hauptstruktur: AcI (Akkusativ mit Infinitiv), abhängig von 'indicat'.\n• 'inusitata... magnitudine' ist ein Ablativus qualitatis (Beschreibt die Eigenschaft der Wolke).\n• 'indicat' steht im historischen Präsens (Übersetzung: Imperfekt/Präteritum)."},
    {"satz_id": 3, "latein": "Poscit soleas, ascendit locum, ex quo maxime miraculum illud conspici poterat.", "loesung": "Er verlangte seine Sandalen und stieg zu einem erhöhten Punkt hinauf, von dem aus man dieses Naturwunder am besten beobachten konnte.", "vokabeln": "poscere = fordern\nsoleae = Sandalen\nascendere = hinaufsteigen\nlocus = Ort / Anhöhe\nconspicere = betrachten", "grammatik": "• Asyndetische Beiordnung ('Poscit..., ascendit...'): Beide Verben stehen im historischen Präsens.\n• 'ex quo' leitet einen Relativsatz ein (Bezugswort: locum).\n• 'conspici poterat' = Passiv-Infinitiv ('betrachtet werden konnte')."},
    {"satz_id": 4, "latein": "Nubes — incertum procul intuentibus, ex quo monte (Vesuvium fuisse postea cognitum est) — oriebatur, cuius similitudinem et formam non alia magis arbor quam pinus expresserit.", "loesung": "Die Wolke stieg empor – für die Beobachter aus der Ferne war unklar, von welchem Berg sie ausging (erst später erfuhr man, dass es der Vesuv war) –, und kein anderer Baum hätte ihre Form und Gestalt besser nachgebildet als eine Pinie.", "vokabeln": "oriri = aufsteigen\nprocul = von fern\nintueri = betrachten\npinus = Pinie\nexpresserit = nachgebildet / ausgedrückt", "grammatik": "• 'intuentibus' = PPA im Dativ Plural (substantiviert: 'für die Beobachter').\n• Eingeschobener AcI in der Klammer: 'Vesuvium fuisse' (dass es der Vesuv gewesen war).\n• 'expresserit' = Konjunktiv Perfekt (Potentialis: 'hätte wohl nachgebildet')."},
    {"satz_id": 5, "latein": "Nam longissimo velut trunco elata in altum quibusdam ramis diffundebatur, credo, quia recenti spiritu evecta, dein senescente eo destituta aut etiam pondere suo victa in latitudinem vanescebat.", "loesung": "Denn wie auf einem enorm langen Stamm schoss sie in die Höhe und verzweigte sich dann in verschiedene Äste; ich glaube, weil sie durch den frischen Druck der Eruption emporgetrieben, dann aber, als dieser nachließ, sich selbst überlassen oder gar von ihrer eigenen Last bezwungen, in die Breite zerfloss.", "vokabeln": "velut = wie\ntruncus = Stamm\nelatus = emporgehoben\nspiritus = Druck / Hauch\nvincere = bezwingen\nvanescere = zerfließen", "grammatik": "• Viele Partizipien (PPP) beziehen sich auf 'nubes' (elata, evecta, destituta, victa).\n• Zwei Ablativi absoluti: 'recenti spiritu' und 'senescente eo' (beschreiben die Ursachen des Wolkenverhaltens)."}
]

DB_FILE = "datenbank.csv"

# ---- 2. KI FUNKTIONEN ----
def initialisiere_ki():
    # Holt Key aus den Streamlit Secrets
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.5-flash')
    except:
        return None

def kontrolliere_rate_limit():
    aktuelle_zeit = time.time()
    if "globaler_anfrage_verlauf" not in st.session_state: st.session_state.globaler_anfrage_verlauf = []
    st.session_state.globaler_anfrage_verlauf = [t for t in st.session_state.globaler_anfrage_verlauf if aktuelle_zeit - t < 60]
    
    if len(st.session_state.globaler_anfrage_verlauf) >= 3: time.sleep(1.5)
    if len(st.session_state.globaler_anfrage_verlauf) >= 4:
        platzhalter = st.empty()
        for i in range(8, 0, -1):
            platzhalter.warning(f"⏳ Der KI-Lehrer korrigiert gerade zeitgleich eine andere Gruppe ({i}s)...")
            time.sleep(1)
        platzhalter.empty()
    st.session_state.globaler_anfrage_verlauf.append(time.time())

def frage_ki_assistent(model, frage, satz_daten):
    kontrolliere_rate_limit()
    prompt = f"Du bist ein Lateinlehrer. Schüler übersetzt: '{satz_daten['latein']}'. Grammatik: {satz_daten['grammatik']}. Frage: '{frage}'. Antworte kurz und präzise, ohne die Lösung zu verraten!"
    try:
        return model.generate_content(prompt).text
    except: return "⏳ Der KI-Lehrer sortiert kurz seine Unterlagen. Bitte erneut versuchen!"

def bewerte_uebersetzung(model, eingabe, satz_daten):
    kontrolliere_rate_limit()
    prompt = f"Latein: '{satz_daten['latein']}'. Lösung: '{satz_daten['loesung']}'. Schüler: '{eingabe}'. Bewerte 0-100. Format: PUNKTZAHL|BEGRÜNDUNG."
    try:
        res = model.generate_content(prompt).text
        return int(res.split("|")[0]), res.split("|")[1]
    except: return 0, "KI-Fehler. Bitte erneut klicken."

# ---- 3. UI ----
st.set_page_config(page_title="Plinius Quiz", layout="wide")
ki_model = initialisiere_ki()

st.title("📜 Plinius: Übersetzungs-Challenge")

if "schueler_name" not in st.session_state:
    name = st.text_input("Dein Team-Name:")
    if st.button("Starten") and name:
        st.session_state.schueler_name = name
        st.session_state.aktueller_satz = 0
        st.session_state.ki_fragen_pro_satz = {}
        st.rerun()
else:
    idx = st.session_state.aktueller_satz
    if idx >= len(SAETZE): st.success("🎉 Fertig!"); st.stop()
    
    s = SAETZE[idx]
    st.info(f"**Latein:** {s['latein']}")
    uebersetzung = st.text_area("Deine Übersetzung:", key=f"t_{idx}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.checkbox("Hilfen anzeigen (-25 Pkt)"):
            st.write("**Vokabeln:**", s['vokabeln'])
            st.write("**Grammatik:**", s['grammatik'])
    with col2:
        if ki_model:
            frage = st.text_input("Frage an den KI-Lehrer (-50 Pkt):")
            if st.button("Fragen"):
                st.info(frage_ki_assistent(ki_model, frage, s))
    
    if st.button("Überprüfen"):
        p, f = bewerte_uebersetzung(ki_model, uebersetzung, s)
        st.write(f"### {p}/100: {f}")
        if p >= 70 and st.button("Nächster Satz"):
            st.session_state.aktueller_satz += 1
            st.rerun()