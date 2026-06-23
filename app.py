import streamlit as st
import pandas as pd
import time
import os
import google.generativeai as genai

# --- 1. KONFIGURATION & DATENBASIS ---
DB_FILE = "datenbank.csv"
ADMIN_PASSWORT = "Lucas2010"

# Die vollständigen Sätze wie in deiner lokalen Wunschversion
SAETZE = [
    {
        "satz_id": 1, 
        "latein": "Erat Miseni classemque imperio praesens regebat.", 
        "loesung": "Er war in Misenum und befehligte dort persönlich die Flotte.", 
        "vokabeln": "• erat Miseni = er war in Misenum\n• classis, is f = Flotte\n• imperio (Abl.) = mit der Befehlsgewalt\n• praesens = anwesend / persönlich", 
        "grammatik": "• 'Miseni' ist ein Lokativ (Antwort auf 'Wo?').\n• 'imperio' steht im Ablativus instrumentalis (Wodurch? -> mit Befehlsgewalt).\n• 'praesens' wirkt hier prädikativ, am besten mit 'persönlich' oder 'selbst' übersetzen."
    },
    {
        "satz_id": 2, 
        "latein": "Nonum kal. Septembres hora fere septima mater mea indicat ei apparere nubem inusitata et magnitudine et specie.", 
        "loesung": "Am 24. August, etwa gegen ein Uhr mittags, wies meine Mutter ihn darauf hin, dass eine Wolke von ungewöhnlicher Größe und Gestalt auftauchte.", 
        "vokabeln": "• nonum kal. Septembres = am 24. August\n• hora fere septima = ca. 13 Uhr\n• indicat = wies hin / meldete\n• apparere = erscheinen", 
        "grammatik": "• Hauptstruktur: AcI (Akkusativ mit Infinitiv), abhängig von 'indicat'.\n• 'inusitata... magnitudine' ist ein Ablativus qualitatis (Beschreibt die Eigenschaft der Wolke).\n• 'indicat' steht im historischen Präsens (Übersetzung: Imperfekt/Präteritum)."
    },
    {
        "satz_id": 3, 
        "latein": "Poscit soleas, ascendit locum, ex quo maxime miraculum illud conspici poterat.", 
        "loesung": "Er verlangte seine Sandalen und stieg zu einem erhöhten Punkt hinauf, von dem aus man dieses Naturwunder am besten beobachten konnte.", 
        "vokabeln": "• poscere = fordern\n• soleae = Sandalen\n• ascendere = hinaufsteigen\n• locus = Ort / Anhöhe\n• conspicere = betrachten", 
        "grammatik": "• Asyndetische Beiordnung ('Poscit..., ascendit...'): Beide Verben stehen im historischen Präsens.\n• 'ex quo' leitet einen Relativsatz ein (Bezugswort: locum).\n• 'conspici poterat' = Passiv-Infinitiv ('betrachtet werden konnte')."
    },
    {
        "satz_id": 4, 
        "latein": "Nubes — incertum procul intuentibus, ex quo monte (Vesuvium fuisse postea cognitum est) — oriebatur, cuius similitudinem et formam non alia magis arbor quam pinus expresserit.", 
        "loesung": "Die Wolke stieg empor – für die Beobachter aus der Ferne war unklar, von welchem Berg sie ausging (erst später erfuhr man, dass es der Vesuv war) –, und kein anderer Baum hätte ihre Form und Gestalt besser nachgebildet als eine Pinie.", 
        "vokabeln": "• oriri = aufsteigen\n• procul = von fern\n• intueri = betrachten\n• pinus = Pinie\n• expresserit = nachgebildet / ausgedrückt", 
        "grammatik": "• 'intuentibus' = PPA im Dativ Plural (substantiviert: 'für die Beobachter').\n• Eingeschobener AcI in der Klammer: 'Vesuvium fuisse' (dass es der Vesuv gewesen war).\n• 'expresserit' = Konjunktiv Perfekt (Potentialis: 'hätte wohl nachgebildet')."
    },
    {
        "satz_id": 5, 
        "latein": "Nam longissimo velut trunco elata in altum quibusdam ramis diffundebatur, credo, quia recenti spiritu evecta, dein senescente eo destituta aut etiam pondere suo victa in latitudinem vanescebat.", 
        "loesung": "Denn wie auf einem enorm langen Stamm schoss sie in die Höhe und verzweigte sich dann in verschiedene Äste; ich glaube, weil sie durch den frischen Druck der Eruption emporgetrieben, dann aber, als dieser nachließ, sich selbst überlassen oder gar von ihrer eigenen Last bezwungen, in die Breite zerfloss.", 
        "vokabeln": "• velut = wie\n• truncus = Stamm\n• elatus = emporgehoben\n• spiritus = Druck / Hauch\n• vincere = bezwingen\n• vanescere = zerfließen", 
        "grammatik": "• Viele Partizipien (PPP) beziehen sich auf 'nubes' (elata, evecta, destituta, victa).\n• Zwei Ablativi absoluti: 'recenti spiritu' und 'senescente eo' (beschreiben die Ursachen des Wolkenverhaltens)."
    }
]

# --- 2. SESSION STATE INITIALISIERUNG ---
if "satz_index" not in st.session_state: st.session_state.satz_index = 0
if "total_punkte" not in st.session_state: st.session_state.total_punkte = 0
if "user_name" not in st.session_state: st.session_state.user_name = ""

# --- 3. KI- & HILFSFUNKTIONEN ---
def initialisiere_ki():
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception:
        return None

def bewerte_uebersetzung(model, eingabe, satz_daten):
    prompt = f"Du bist ein Lateinlehrer. Bewerte die Übersetzung des Schülers. \nLateinischer Text: '{satz_daten['latein']}'\nLösung: '{satz_daten['loesung']}'\nSchülerübersetzung: '{eingabe}'\nGib mir eine Punktzahl von 0 bis 100 und eine kurze, präzise Begründung (max 2 Sätze). Antworte im Format: PUNKTZAHL|BEGRÜNDUNG"
    try:
        antwort = model.generate_content(prompt).text
        teile = antwort.split("|")
        return int(teile[0]), teile[1]
    except:
        return 0, "KI konnte aktuell nicht antworten."

# --- 4. DATENBANK-FUNKTIONEN ---
def speichere_ergebnis(name, punkte):
    df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame(columns=["Name", "Punkte"])
    df = pd.concat([df, pd.DataFrame([{"Name": name, "Punkte": punkte}])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# --- 5. UI-LOGIK ---
st.set_page_config(page_title="Plinius Quiz", layout="wide")
model = initialisiere_ki()

page = st.sidebar.radio("Navigation", ["Quiz", "Admin-Panel"])

if page == "Admin-Panel":
    if st.sidebar.text_input("Admin-Passwort", type="password") == ADMIN_PASSWORT:
        st.title("🏆 Live-Rangliste (Tafel-Modus)")
        if st.button("Datenbank zurücksetzen"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE); st.rerun()
        if os.path.exists(DB_FILE):
            df = pd.read_csv(DB_FILE).groupby("Name")["Punkte"].sum().sort_values(ascending=False).reset_index()
            st.table(df)
        time.sleep(5); st.rerun()
    else: st.warning("Zugriff verweigert.")

else:
    st.title("📜 Plinius: Übersetzungs-Challenge")
    if not st.session_state.user_name:
        st.session_state.user_name = st.text_input("Name:")
        if st.button("Start"): st.rerun()
    else:
        idx = st.session_state.satz_index
        if idx < len(SAETZE):
            s = SAETZE[idx]
            st.info(f"**Satz {idx+1}:** {s['latein']}")
            eingabe = st.text_area("Deine Übersetzung:", key=f"inp_{idx}")
            if st.checkbox("Tipps anzeigen"):
                st.write("#### Vokabeln")
                st.write(s['vokabeln'])
                st.write("#### Grammatik")
                st.write(s['grammatik'])
            if st.button("Überprüfen"):
                p, k = bewerte_uebersetzung(model, eingabe, s)
                st.write(f"### Bewertung: {p}/100 Pkt")
                st.write(k)
                if st.button("Nächster"):
                    st.session_state.total_punkte += p
                    st.session_state.satz_index += 1
                    st.rerun()
        else:
            speichere_ergebnis(st.session_state.user_name, st.session_state.total_punkte)
            st.success(f"Fertig! Dein Score: {st.session_state.total_punkte}")