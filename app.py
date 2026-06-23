import streamlit as st
import pandas as pd
import time
import os
import google.generativeai as genai

# --- KONFIGURATION ---
DB_FILE = "datenbank.csv"
ADMIN_PASSWORT = "Lucas2010"

SAETZE = [
    {"satz_id": 1, "latein": "Erat Miseni classemque imperio praesens regebat.", "loesung": "Er war in Misenum und befehligte dort persönlich die Flotte.", "vokabeln": "erat Miseni = er war in Misenum\nclassis, is f = Flotte\nimperio (Abl.) = mit der Befehlsgewalt\npraesens = anwesend / persönlich", "grammatik": "• 'Miseni' ist ein Lokativ (Antwort auf 'Wo?').\n• 'imperio' steht im Ablativus instrumentalis (Wodurch? -> mit Befehlsgewalt).\n• 'praesens' wirkt hier prädikativ, am besten mit 'persönlich' übersetzen."},
    {"satz_id": 2, "latein": "Nonum kal. Septembres hora fere septima mater mea indicat ei apparere nubem inusitata et magnitudine et specie.", "loesung": "Am 24. August, etwa gegen ein Uhr mittags, wies meine Mutter ihn darauf hin, dass eine Wolke von ungewöhnlicher Größe und Gestalt auftauchte.", "vokabeln": "nonum kal. Septembres = am 24. August\nhora fere septima = ca. 13 Uhr\nindicat = wies hin / meldete\napparere = erscheinen", "grammatik": "• Hauptstruktur: AcI (Akkusativ mit Infinitiv), abhängig von 'indicat'.\n• 'inusitata... magnitudine' ist ein Ablativus qualitatis (Beschreibt die Eigenschaft der Wolke).\n• 'indicat' steht im historischen Präsens (Übersetzung: Präteritum)."},
    {"satz_id": 3, "latein": "Poscit soleas, ascendit locum, ex quo maxime miraculum illud conspici poterat.", "loesung": "Er verlangte seine Sandalen und stieg zu einem erhöhten Punkt hinauf, von dem aus man dieses Naturwunder am besten beobachten konnte.", "vokabeln": "poscere = fordern\nsoleae = Sandalen\nascendere = hinaufsteigen\nlocus = Ort / Anhöhe\nconspicere = betrachten", "grammatik": "• Asyndetische Beiordnung: Beide Verben stehen im historischen Präsens.\n• 'ex quo' leitet einen Relativsatz ein.\n• 'conspici poterat' = Passiv-Infinitiv ('betrachtet werden konnte')."},
    {"satz_id": 4, "latein": "Nubes — incertum procul intuentibus, ex quo monte (Vesuvium fuisse postea cognitum est) — oriebatur, cuius similitudinem et formam non alia magis arbor quam pinus expresserit.", "loesung": "Die Wolke stieg empor – für die Beobachter aus der Ferne war unklar, von welchem Berg sie ausging (erst später erfuhr man, dass es der Vesuv war) –, und kein anderer Baum hätte ihre Form und Gestalt besser nachgebildet als eine Pinie.", "vokabeln": "oriri = aufsteigen\nprocul = von fern\nintueri = betrachten\npinus = Pinie\nexpresserit = nachgebildet / ausgedrückt", "grammatik": "• 'intuentibus' = PPA im Dativ Plural (substantiviert: 'für die Beobachter').\n• Eingeschobener AcI: 'Vesuvium fuisse' (dass es der Vesuv gewesen war).\n• 'expresserit' = Konjunktiv Perfekt (Potentialis: 'hätte wohl nachgebildet')."},
    {"satz_id": 5, "latein": "Nam longissimo velut trunco elata in altum quibusdam ramis diffundebatur, credo, quia recenti spiritu evecta, dein senescente eo destituta aut etiam pondere suo victa in latitudinem vanescebat.", "loesung": "Denn wie auf einem enorm langen Stamm schoss sie in die Höhe und verzweigte sich dann in verschiedene Äste; ich glaube, weil sie durch den frischen Druck der Eruption emporgetrieben, dann aber, als dieser nachließ, sich selbst überlassen oder gar von ihrer eigenen Last bezwungen, in die Breite zerfloss.", "vokabeln": "velut = wie\ntruncus = Stamm\nelatus = emporgehoben\nspiritus = Druck / Hauch\nvincere = bezwingen\nvanescere = zerfließen", "grammatik": "• Viele Partizipien (PPP) beziehen sich auf 'nubes'.\n• Zwei Ablativi absoluti: 'recenti spiritu' und 'senescente eo' (beschreiben Ursachen des Wolkenverhaltens)."}
]

# --- KI LOGIK ---
def initialisiere_ki():
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-2.5-flash')
    except: return None

def kontrolliere_rate_limit():
    aktuelle_zeit = time.time()
    if "globaler_anfrage_verlauf" not in st.session_state: st.session_state.globaler_anfrage_verlauf = []
    st.session_state.globaler_anfrage_verlauf = [t for t in st.session_state.globaler_anfrage_verlauf if aktuelle_zeit - t < 60]
    if len(st.session_state.globaler_anfrage_verlauf) >= 3: time.sleep(1.5)
    st.session_state.globaler_anfrage_verlauf.append(time.time())

# --- DATENBANK ---
def lade_daten():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Name", "Uebersetzungs_Punkte", "Fertig"])

def speichere_daten(name, punkte):
    df = lade_daten()
    df = pd.concat([df, pd.DataFrame([{"Name": name, "Uebersetzungs_Punkte": punkte, "Fertig": True}])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# --- UI ---
st.set_page_config(page_title="Plinius Quiz", layout="wide")
ki_model = initialisiere_ki()

page = st.sidebar.radio("Navigation", ["Quiz", "Admin-Panel"])

if page == "Admin-Panel":
    pw = st.sidebar.text_input("Admin-Passwort", type="password")
    if pw == ADMIN_PASSWORT:
        st.title("🏆 LIVE-RANGLISTE")
        if st.button("Datenbank zurücksetzen"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.rerun()
        
        # Kahoot-Style Anzeige
        df = lade_daten()
        if not df.empty:
            df = df.groupby("Name")["Uebersetzungs_Punkte"].sum().reset_index().sort_values(by="Uebersetzungs_Punkte", ascending=False)
            st.table(df)
        else: st.write("Noch keine Daten.")
        time.sleep(5); st.rerun()
    else: st.warning("Zugriff verweigert.")

else:
    st.title("📜 Plinius & der Vesuv")
    if "name" not in st.session_state:
        name = st.text_input("Team-Name:")
        if st.button("Start"): st.session_state.name = name; st.rerun()
    else:
        idx = st.session_state.get("satz_idx", 0)
        if idx < len(SAETZE):
            s = SAETZE[idx]
            st.info(f"**Latein:** {s['latein']}")
            eingabe = st.text_area("Übersetzung:")
            if st.button("Überprüfen"):
                kontrolliere_rate_limit()
                # Einfache Punkte-Logik für Demo
                punkte = 80 
                st.session_state.punkte = st.session_state.get("punkte", 0) + punkte
                if st.button("Nächster"): 
                    st.session_state.satz_idx = idx + 1
                    st.rerun()
        else:
            speichere_daten(st.session_state.name, st.session_state.get("punkte", 0))
            st.success("Fertig!")