import streamlit as st
import pandas as pd
import time
import os
import google.generativeai as genai

# --- 1. DATENBASIS ---
SAETZE = [
    {
        "satz_id": 1,
        "latein": "Erat Miseni classemque imperio praesens regebat.",
        "loesung": "Er war in Misenum und befehligte dort persönlich die Flotte.",
        "vokabeln": "erat Miseni = er war in Misenum\nclassis, is f = Flotte\nimperio (Abl.) = mit der Befehlsgewalt\npraesens = anwesend / persönlich",
        "grammatik": "• 'Miseni' ist ein Lokativ (Ortsangabe auf die Frage: 'Wo?'). Bei Städten und kleinen Inseln der o-Deklination im Singular nutzt Latein dafür die Genitiv-Endung.\n• 'classem' ist das direkte Akkusativ-Objekt zu 'regebat'.\n• 'imperio' steht im Ablativus instrumentalis (Womit/Wodurch befehligte er? -> Mit Befehlsgewalt).\n• 'praesens' ist ein Partizip/Adjektiv, das hier prädikativ gebraucht wird. Im Deutschen übersetzt man das nicht starr mit 'anwesend', sondern als Adverb: 'er befehligte persönlich' oder 'er war selbst vor Ort'."
    },
    {
        "satz_id": 2,
        "latein": "Nonum kal. Septembres hora fere septima mater mea indicat ei apparere nubem inusitata et magnitudine et specie.",
        "loesung": "Am 24. August, etwa gegen ein Uhr mittags, wies meine Mutter ihn darauf hin, dass eine Wolke von ungewöhnlicher Größe und Gestalt auftauchte.",
        "vokabeln": "nonum kal. Septembres = am 24. August\nhora fere septima = ungefähr in der 7. Stunde (ca. 13 Uhr)\nindicat = (hier historisches Präsens) wies hin / meldete\napparere = erscheinen / auftauchen\nnubes, is f = Wolke\ninusitatus, a, um = ungewöhnlich\nmagnitudo, inis f = Größe\nspecies, ei f = Gestalt / Aussehen",
        "grammatik": "• Kernstruktur des Satzes ist ein AcI (Akkusativ mit Infinitiv), abhängig vom Kopfverb 'indicat' ('meine Mutter weist darauf hin, dass...').\n• Der Subjektsakkusativ des AcI ist 'nubem', der Infinitiv ist 'apparere'.\n• 'inusitata et magnitudine et specie' ist ein Ablativus qualitatis (Ablativ der Eigenschaft). Er beschreibt die Wolke näher. Das 'et... et...' bedeutet hier 'sowohl... als auch...' oder schlicht 'und'.\n• Das Prädikat 'indicat' steht im historischen Präsens, um die Erzählung lebendig zu machen. Übersetze es im Deutschen im Präteritum ('wies hin')."
    },
    {
        "satz_id": 3,
        "latein": "Poscit soleas, ascendit locum, ex quo maxime miraculum illud conspici poterat.",
        "loesung": "Er verlangte seine Sandalen und stieg zu einem erhöhten Punkt hinauf, von dem aus man dieses Naturwunder am besten beobachten konnte.",
        "vokabeln": "poscere = fordern / verlangen\nsoleae, arum f = Sandalen\nascendere = besteigen / hinaufsteigen\nlocus, i m = Ort / (hier:) Anhöhe\nex quo = von wo aus / von dem aus\nmaxime = am besten / am meisten\nmiraculum, i n = Wunder / Naturwunder\nconspicere = erblicken / betrachten",
        "grammatik": "• Der Satz besteht aus einer Reihung (Asyndetische Beiordnung): 'Poscit..., ascendit...'. Beide Verben stehen im historischen Präsens (Präteritum nutzen!).\n• 'ex quo' leitet einen Relativsatz ein, der sich auf das Bezugswort 'locum' bezieht. 'quo' ist ein Ablativ (Masc. Sing.) nach der Präposition 'ex'.\n• 'conspici poterat' ist eine Passiv-Konstruktion. 'conspici' ist der Infinitiv Präsens Passiv ('betrachtet werden'). Zusammen mit 'poterat' (3. Pers. Sing. Imperfekt von posse) heißt es: 'konnte betrachtet werden' oder aktivischer: 'man konnte beobachten'."
    },
    {
        "satz_id": 4,
        "latein": "Nubes — incertum procul intuentibus, ex quo monte (Vesuvium fuisse postea cognitum est) — oriebatur, cuius similitudinem et formam non alia magis arbor quam pinus expresserit.",
        "loesung": "Die Wolke stieg empor – für die Beobachter aus der Ferne war unklar, von welchem Berg sie ausging (erst später erfuhr man, dass es der Vesuv war) –, und kein anderer Baum hätte ihre Form und Gestalt besser nachgebildet als eine Pinie.",
        "vokabeln": "oriri = aufsteigen / entstehen\nincertus, a, um = unklar / ungewiss\nprocul = von fern / aus der Ferne\nintueri = betrachten / anschauen\npostea = später\ncognoscere = erkennen / erfahren\nsimilitudo, inis f = Ähnlichkeit / Form\narbor, oris f = Baum\npinus, i f = Pinie\nexprimere = nachbilden / ausdrücken",
        "grammatik": "• 'intuentibus' ist ein PPA (Partizip Präsens Aktiv) im Dativ Plural. Es ist substantiviert gebraucht: 'für die Betrachtenden' / 'für die Beobachter'.\n• 'ex quo monte ... [oriebatur]' ist eine indirekte Frageabhängigkeit, ausgelöst durch das eingeschobene 'incertum [erat]'.\n• 'Vesuvium fuisse' ist ein perfektischer AcI in der Klammer, abhängig von 'cognitum est' ('es wurde bekannt / man erfuhr, dass es der Vesuv gewesen war').\n• 'cuius' ist ein relatives Satzanschluss-Pronomen im Genitiv (Bezugswort: nubes) -> 'deren Ähnlichkeit...'.\n• 'expresserit' steht im Konjunktiv Perfekt und fungiert hier als Potentialis der Gegenwart: 'hätte wohl ausgedrückt' oder 'hätte besser nachgebildet'."
    },
    {
        "satz_id": 5,
        "latein": "Nam longissimo velut trunco elata in altum quibusdam ramis diffundebatur, credo, quia recenti spiritu evecta, dein senescente eo destituta aut etiam pondere suo victa in latitudinem vanescebat.",
        "loesung": "Denn wie auf einem enorm langen Stamm schoss sie in die Höhe und verzweigte sich dann in verschiedene Äste; ich glaube, weil sie durch den frischen Druck der Eruption emporgetrieben, dann aber, als dieser nachließ, sich selbst überlassen oder gar von ihrer eigenen Last bezwungen, in die Breite zerfloss.",
        "vokabeln": "velut = wie / gleichsam\ntruncus, i m = Stamm\nelatus, a, um = emporgehoben / hochgetragen\naltum, i n = die Höhe\nramus, i m = Ast / Zweig\ndiffundere = ausbreiten / verzweigen\nrecens, ntis = frisch / neu\nspiritus, us m = Hauch / Druck / Wind\nevehere = emportragen\nsenescere = alt werden / nachlassen\ndestituere = im Stich lassen / einsam zurücklassen\npondus, eris n = Gewicht / Last / Masse\nvincere = besiegen / bezwingen\nvanescere = schwinden / zerfließen",
        "grammatik": "• Der Satz wimmelt nur so von Partizipien (PPP), die sich alle als Attribute auf das Subjekt 'nubes' (die Wolke, Femininum) beziehen: 'elata' (emporgehoben), 'evecta' (emporgetrieben), 'destituta' (verlassen) und 'victa' (bezwungen). Diese löst man im Deutschen am besten durch aktive Verben im Nebensatz auf.\n• 'longissimo trunco' ist ein Ablativus instrumentalis (Womit/Worauf erhob sie sich? -> Auf einem sehr langen Stamm).\n• Es liegen zwei Ablativi absoluti (Abl. abs.) vor:\n  1. 'recenti spiritu' (Nominaler Abl. abs. -> 'durch den frischen Druck / Lufthauch').\n  2. 'senescente eo' (Partizipialer Abl. abs. mit PPA -> 'während dieser [der Wind/Druck] nachließ' / 'als dieser abflachte')."
    }
]

DB_FILE = "datenbank.csv"

# --- 2. HILFSFUNKTIONEN (KI & RATE-LIMIT) ---
def initialisiere_ki(api_key):
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception: return None

def kontrolliere_rate_limit():
    aktuelle_zeit = time.time()
    if "globaler_anfrage_verlauf" not in st.session_state: st.session_state.globaler_anfrage_verlauf = []
    st.session_state.globaler_anfrage_verlauf = [t for t in st.session_state.globaler_anfrage_verlauf if aktuelle_zeit - t < 60]
    if len(st.session_state.globaler_anfrage_verlauf) >= 3: time.sleep(1.5)
    if len(st.session_state.globaler_anfrage_verlauf) >= 4:
        with st.empty():
            for i in range(8, 0, -1):
                st.warning(f"⏳ Der KI-Lehrer korrigiert zeitgleich für andere Teams. Geduld: {i}s...")
                time.sleep(1)
    st.session_state.globaler_anfrage_verlauf.append(time.time())

def frage_ki_assistent(model, frage, satz_daten):
    kontrolliere_rate_limit()
    prompt = f"Du bist ein Lateinlehrer. Satz: '{satz_daten['latein']}'. Grammatik: {satz_daten['grammatik']}. Frage: '{frage}'. Antworte kurz und präzise auf Deutsch, ohne das Ergebnis zu verraten."
    return model.generate_content(prompt).text

def bewerte_uebersetzung(model, eingabe, satz_daten):
    kontrolliere_rate_limit()
    prompt = f"Satz: '{satz_daten['latein']}'. Lösung: '{satz_daten['loesung']}'. Schüler: '{eingabe}'. Bewerte (0-100). Format: PUNKTZAHL|BEGRÜNDUNG."
    res = model.generate_content(prompt).text
    p = int(res.split("|")[0]) if "|" in res else 50
    f = res.split("|")[1] if "|" in res else res
    return p, f

# --- 3. DATENBANK & UI ---
def speichere_daten(name, satz_id, dauer, punkte, h1, h_ki, fertig=False):
    df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame(columns=["Name", "Satz_ID", "Dauer", "Uebersetzungs_Punkte", "Hilfe_Stufe1", "Hilfe_KI", "Fertig"])
    df = pd.concat([df, pd.DataFrame([{"Name": name, "Satz_ID": satz_id, "Dauer": dauer, "Uebersetzungs_Punkte": punkte, "Hilfe_Stufe1": h1, "Hilfe_KI": h_ki, "Fertig": fertig}])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

st.set_page_config(page_title="Plinius Quiz", layout="wide")

# Sidebar für Admin & API
with st.sidebar:
    st.header("⚙️ Verwaltung")
    pw = st.text_input("Admin-Passwort", type="password")
    api_key = st.text_input("Gemini API-Key", type="password")
    ki_model = initialisiere_ki(api_key) if api_key else None

if pw == "Lucas2010":
    st.title("🏆 Live-Rangliste (Admin-Panel)")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        if not df.empty:
            rangliste = df.groupby("Name")["Uebersetzungs_Punkte"].sum().sort_values(ascending=False).reset_index()
            st.table(rangliste)
    if st.button("Datenbank löschen"): os.remove(DB_FILE); st.rerun()
    time.sleep(5); st.rerun()
else:
    # --- QUIZ LOGIK ---
    if "name" not in st.session_state:
        st.session_state.name = st.text_input("Team-Name:")
        if st.button("Start"): st.session_state.s_idx = 0; st.rerun()
    else:
        idx = st.session_state.s_idx
        if idx < len(SAETZE):
            s = SAETZE[idx]
            st.info(f"**Satz {idx+1}:** {s['latein']}")
            eingabe = st.text_area("Übersetzung:", key=f"t_{idx}")
            if st.checkbox("Tipps zeigen"):
                st.write("**Vokabeln:**", s['vokabeln'])
                st.write("**Grammatik:**", s['grammatik'])
            if st.button("Überprüfen"):
                p, f = bewerte_uebersetzung(ki_model, eingabe, s)
                st.write(f"### Bewertung: {p}/100")
                st.write(f)
                if st.button("Nächster"):
                    st.session_state.s_idx += 1
                    st.rerun()
        else: st.success("Quiz beendet!")