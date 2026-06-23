import streamlit as st
import pandas as pd
import time
import os
import google.generativeai as genai

# --- 1. KONFIGURATION & DATENBASIS ---
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
        "grammatik": "• Kernstruktur des Satzes ist ein AcI (Akkusativ mit Infinitiv), abhängig vom Kopfverb 'indicat'.\n• 'inusitata et magnitudine et specie' ist ein Ablativus qualitatis (Ablativ der Eigenschaft).\n• Das Prädikat 'indicat' steht im historischen Präsens, um die Erzählung lebendig zu machen. Übersetze es im Deutschen im Präteritum ('wies hin')."
    },
    {
        "satz_id": 3,
        "latein": "Poscit soleas, ascendit locum, ex quo maxime miraculum illud conspici poterat.",
        "loesung": "Er verlangte seine Sandalen und stieg zu einem erhöhten Punkt hinauf, von dem aus man dieses Naturwunder am besten beobachten konnte.",
        "vokabeln": "poscere = fordern / verlangen\nsoleae, arum f = Sandalen\nascendere = besteigen / hinaufsteigen\nlocus, i m = Ort / (hier:) Anhöhe\nex quo = von wo aus / von dem aus\nmaxime = am besten / am meisten\nmiraculum, i n = Wunder / Naturwunder\nconspicere = erblicken / betrachten",
        "grammatik": "• Asyndetische Beiordnung ('Poscit..., ascendit...'). Beide Verben stehen im historischen Präsens.\n• 'conspici poterat' ist eine Passiv-Konstruktion ('konnte betrachtet werden')."
    },
    {
        "satz_id": 4,
        "latein": "Nubes — incertum procul intuentibus, ex quo monte (Vesuvium fuisse postea cognitum est) — oriebatur, cuius similitudinem et formam non alia magis arbor quam pinus expresserit.",
        "loesung": "Die Wolke stieg empor – für die Beobachter aus der Ferne war unklar, von welchem Berg sie ausging (erst später erfuhr man, dass es der Vesuv war) –, und kein anderer Baum hätte ihre Form und Gestalt besser nachgebildet als eine Pinie.",
        "vokabeln": "oriri = aufsteigen / entstehen\nincertus, a, um = unklar / ungewiss\nprocul = von fern / aus der Ferne\nintueri = betrachten / anschauen\npostea = später\ncognoscere = erkennen / erfahren\nsimilitudo, inis f = Ähnlichkeit / Form\narbor, oris f = Baum\npinus, i f = Pinie\nexprimere = nachbilden / ausdrücken",
        "grammatik": "• 'intuentibus' ist ein PPA (Partizip Präsens Aktiv) im Dativ Plural (substantiviert).\n• 'Vesuvium fuisse' ist ein AcI in der Klammer, abhängig von 'cognitum est'.\n• 'expresserit' steht im Konjunktiv Perfekt (Potentialis der Gegenwart)."
    },
    {
        "satz_id": 5,
        "latein": "Nam longissimo velut trunco elata in altum quibusdam ramis diffundebatur, credo, quia recenti spiritu evecta, dein senescente eo destituta aut etiam pondere suo victa in latitudinem vanescebat.",
        "loesung": "Denn wie auf einem enorm langen Stamm schoss sie in die Höhe und verzweigte sich dann in verschiedene Äste; ich glaube, weil sie durch den frischen Druck der Eruption emporgetrieben, dann aber, als dieser nachließ, sich selbst überlassen oder gar von ihrer eigenen Last bezwungen, in die Breite zerfloss.",
        "vokabeln": "velut = wie / gleichsam\ntruncus, i m = Stamm\nelatus, a, um = emporgehoben\nramus, i m = Ast / Zweig\nrecens, ntis = frisch / neu\nspiritus, us m = Hauch / Druck / Wind\nsenescere = alt werden / nachlassen\nvanescere = schwinden / zerfließen",
        "grammatik": "• Der Satz wimmelt von Partizipien (PPP), die sich alle auf das Subjekt 'nubes' (die Wolke) beziehen.\n• Es liegen zwei Ablativi absoluti vor: 1. 'recenti spiritu' (Nominal) und 2. 'senescente eo' (Partizipial mit PPA)."
    }
]

DB_FILE = "datenbank.csv"

# --- 2. INITIALISIERUNG ---
# WICHTIG: Session State hier initialisieren, damit der Fehler nicht auftritt
if "s_idx" not in st.session_state: st.session_state.s_idx = 0
if "name" not in st.session_state: st.session_state.name = ""

def initialisiere_ki():
    try:
        # Greift direkt auf deine Secrets zu
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception: return None

# --- 3. UI-LOGIK ---
st.set_page_config(page_title="Plinius Quiz", layout="wide")
ki_model = initialisiere_ki()

with st.sidebar:
    st.header("⚙️ Lehrer-Bereich")
    pw = st.text_input("Admin-Passwort", type="password")

if pw == "Lucas2010":
    st.title("🏆 Live-Rangliste (Tafel-Modus)")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        if not df.empty:
            # Zeigt die Rangliste an
            st.table(df.groupby("Name")["Punkte"].sum().sort_values(ascending=False).reset_index())
    if st.button("Datenbank löschen"): os.remove(DB_FILE); st.rerun()
    time.sleep(5); st.rerun()
else:
    st.title("📜 Plinius: Übersetzungs-Challenge")
    if not st.session_state.name:
        st.session_state.name = st.text_input("Team-Name:")
        if st.button("Start"): st.rerun()
    else:
        idx = st.session_state.s_idx
        if idx < len(SAETZE):
            s = SAETZE[idx]
            st.info(f"**Satz {idx+1}:** {s['latein']}")
            eingabe = st.text_area("Deine Übersetzung:", key=f"t_{idx}")
            if st.checkbox("Tipps anzeigen"):
                st.write("**Vokabeln:**", s['vokabeln'])
                st.write("**Grammatik:**", s['grammatik'])
            if st.button("Überprüfen"):
                st.write("Bewertung läuft...") 
                # Hier käme deine Bewertungslogik
                if st.button("Nächster"):
                    st.session_state.s_idx += 1
                    st.rerun()
        else:
            st.success("Herzlichen Glückwunsch, das Quiz ist beendet!")