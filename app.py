import streamlit as st
import pandas as pd
import time
import os
from google import genai  # HIER GEÄNDERT: Das neue Google GenAI SDK importieren

# ---- 1. DATENBASIS: PLINIUS TEXT ----
SAETZE = [
    {
        "satz_id": 1,
        "latein": "Erat Miseni classemque imperio praesens regebat.",
        "loesung": "Er war in Misenum und befehligte dort persönlich die Flotte.",
        "vokabeln": "erat Miseni = er war in Misenum\nclassis, is f = Flotte\nimperio (Abl.) = mit der Befehlsgewalt\npraesens = anwesend / persönlich",
        "grammatik": "• 'Miseni' ist unregelmäßig ein Lokativ (Ortsangabe auf die Frage: 'Wo?'). Bei Städten und kleinen Inseln der o-Deklination im Singular nutzt Latein dafür die Genitiv-Endung.\n• 'classem' ist das direkte Akkusativ-Objekt zu 'regebat'.\n• 'imperio' steht im Ablativus instrumentalis (Womit/Wodurch befehligte er? -> Mit Befehlsgewalt).\n• 'praesens' ist ein Partizip/Adjektiv, das hier prädikativ gebraucht wird. Im Deutschen übersetzt man das nicht starr mit 'anwesend', sondern als Adverb: 'er befehligte persönlich' oder 'er war selbst vor Ort'."
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
        "loesung": "Er verlangte seine Sandalen und stieg zu einem erhöhten Point hinauf, von dem aus man dieses Naturwunder am besten beobachten konnte.",
        "vokabeln": "poscere = fordern / verlangen\nsoleae, arum f = Sandalen\nascendere = besteigen / hinaufsteigen\nlocus, i m = Ort / (hier:) Anhöhe\nex quo = von wo aus / von dem aus\nmaxime = am besten / am meisten\nmiraculum, i n = Wunder / Naturwunder\nconspicere = erblicken / betrachten",
        "grammatik": "• Der Satz besteht aus einer Reihung (Asyndetische Beiordnung): 'Poscit..., ascendit...'. Beide Verben stehen im historischen Präsens (Präteritum nutzen!).\n• 'ex quo' leitet einen Relativsatz ein, der sich auf das Bezugswort 'locum' bezieht. 'quo' ist ein Ablativ (Masc. Sing.) nach der Präposition 'ex'.\n• 'conspici poterat' ist eine Passiv-Konstruktion. 'conspici' ist der Infinitiv Präsens Passiv ('betrachtet werden'). Zusammen mit 'poterat' (3. Pers. Sing. Imperfekt von posse) heißt es: 'konnte betrachtet werden' oder aktivischer: 'man konnte beobachten'."
    },
    {
        "satz_id": 4,
        "latein": "Nubes — incertum procul intuentibus, ex quo monte (Vesuvium fuisse postea cognitum est) — oriebatur, cuius similitudinem et formam non alia magis arbor quam pinus expresserit.",
        "loesung": "Die Wolke stieg empor – für die Beobachter aus der Ferne war unklar, von welchem Berg sie ausging (erst später erfuhr man, dass es der Vesuv war) –, und kein anderer Baum hätte ihre Form und Gestalt besser nachgebildet als eine Pinie.",
        "vokabeln": "oriri = aufsteigen / entstehen\nincertus, a, um = unklar / ungewiss\nprocul = von fern / aus der Ferne\nintueri = betrachten / anschauen\npostea = später\ncognoscere = erkennen / erfahren\nsimilitudo, inis f = Ähnlichkeit / Form\narbor, oris f = Baum\npinus, i f = Pinie\nexprimere = nachbilden / ausdrücken",
        "grammatik": "• 'intuentibus' ist un PPA (Partizip Präsens Aktiv) im Dativ Plural. Es ist substantiviert gebraucht: 'für die Betrachtenden' / 'für die Beobachter'.\n• 'ex quo monte ... [oriebatur]' ist eine indirekte Frageabhängigkeit, ausgelöst durch das eingeschobene 'incertum [erat]'.\n• 'Vesuvium fuisse' ist ein perfektischer AcI in der Klammer, abhängig von 'cognitum est' ('es wurde bekannt / man erfuhr, dass es der Vesuv gewesen war').\n• 'cuius' ist ein relatives Satzanschluss-Pronomen im Genitiv (Bezugswort: nubes) -> 'deren Ähnlichkeit...'.\n• 'expresserit' steht im Konjunktiv Perfekt und fungiert hier als Potentialis der Gegenwart: 'hätte wohl ausgedrückt' oder 'hätte besser nachgebildet'."
    },
    {
        "satz_id": 5,
        "latein": "Nam longissimo velut trunco elata in altum quibusdam ramis diffundebatur, credo, quia recenti spiritu evecta, dein senescente eo destituta aut etiam pondere suo victa in latitudinem vanescebat.",
        "loesung": "Denn wie auf einem enorm langen Stamm schoss sie in die Höhe und verzweigte sich dann in verschiedene Äste; ich glaube, weil sie durch den frischen Druck der Eruption emporgetrieben, dann aber, als dieser nachließ, sich selbst überlassen oder gar von ihrer eigenen Last bezwungen, in die Breite zerfloss.",
        "vokabeln": "velut = wie / gleichsam\ntruncus, i m = Stamm\nelatus, a, um = emporgehoben / hochgetragen\naltum, i n = die Höhe\nramus, i m = Ast / Zweig\ndiffundere = ausbreiten / verzweigen\nrecens, ntis = frisch / neu\nspiritus, us m = Hauch / Druck / Wind\nevehere = emportragen\nsenescere = alt werden / nachlassen\ndestituere = im Stich lassen / einsam zurücklassen\npondus, eris n = Gewicht / Last / Masse\nvincere = besiegen / bezwingen\nvanescere = schwinden / zerfließen",
        "grammatik": "• Der Satz wimmelt nur so von Partizipien (PPP), die sich alle als Attribute auf das Subjekt 'nubes' (die Wolke, Femininum) beziehen: 'elata' (emporgehoben), 'evecta' (emporgetrieben), 'destituta' (verlassen) und 'victa' (bezwungen). Diese löst man im Deutschen am besten durch aktive Verben im Nebensatz auf.\n• 'longissimo trunco' ist ein Ablativus instrumentalis (Womit/Worauf erhob sie sich? -> Auf einem sehr langen Stamm).\n• Es liegen zwei Ablative vor:\n  1. 'recenti spiritu' (Ablativus causae/instrumentalis -> 'durch den frischen Druck / Lufthauch').\n  2. 'senescente eo' (Partizipialer Abl. abs. mit PPA -> 'während dieser [der Wind/Druck] nachlassen' / 'als dieser abflachte')."
    }
]

DB_FILE = "datenbank.csv"

# ---- 2. API KEY HILFSFUNKTION ----
def lade_api_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return ""

# ---- 3. KI FUNKTIONEN MIT MODELL & RATE LIMITER ----
def initialisiere_ki(api_key):
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None

def kontrolliere_rate_limit():
    aktuelle_zeit = time.time()
    if "globaler_anfrage_verlauf" not in st.session_state:
        st.session_state.globaler_anfrage_verlauf = []
        
    st.session_state.globaler_anfrage_verlauf = [
        t for t in st.session_state.globaler_anfrage_verlauf if aktuelle_zeit - t < 60
    ]
    
    anfragen_letzte_minute = len(st.session_state.globaler_anfrage_verlauf)
    
    if anfragen_letzte_minute >= 3:
        time.sleep(1.5)
        
    if anfragen_letzte_minute >= 4:
        platzhalter = st.empty()
        for i in range(8, 0, -1):
            platzhalter.warning(f"⏳ Der KI-Lehrer korrigiert gerade zeitgleich eine andere Gruppe. Bitte gedulde dich {i} Sekunden...")
            time.sleep(1)
        platzhalter.empty()
        
    st.session_state.globaler_anfrage_verlauf.append(time.time())

def frage_ki_assistent(client, frage, satz_daten):
    if not client:
        return "Fehler: KI nicht verbunden. Hat der Lehrer den API-Key in den Secrets hinterlegt?"
    
    kontrolliere_rate_limit()
    
    prompt = f"""Du bist ein freundlicher, motivierender Lateinlehrer an einer Schule.
    Der Schüler übersetzt gerade diesen Satz: '{satz_daten['latein']}'.
    Die exakten Grammatik-Highlights sind: {satz_daten['grammatik']}.
    Der Schüler fragt dich: '{frage}'
    
    Antworte kurz, verständlich und präzise auf Deutsch. Erkläre die grammatikalische Struktur geduldig, aber verrate NIEMALS das fertige deutsche Satz-Ergebnis!"""
    
    try:
        # HIER GEÄNDERT: Korrekter Modell-Name "gemini-1.5-flash"
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
    except Exception:
        return "⏳ Der KI-Lehrer sortiert kurz seine Unterlagen. Bitte formuliere deine Frage in 10 Sekunden noch einmal kurz um!"

def bewerte_uebersetzung(client, schueler_eingabe, satz_daten):
    if not client:
        return 0, "Fehler: KI nicht verbunden."
        
    kontrolliere_rate_limit()
        
    prompt = f"""Du bist ein Lateinlehrer und korrigierst eine Übersetzung.
    Lateinischer Originalsatz: '{satz_daten['latein']}'
    Musterlösung: '{satz_daten['loesung']}'
    
    Übersetzung des Schülers: '{schueler_eingabe}'
    
    Bewerte die Übersetzung des Schülers auf einer Skala von 0 bis 100 Punkten. 
    Sei kulant bei treffenden deutschen Synonymen oder leicht veränderter deutscher Satzstellung, der Sinn muss exakt getroffen sein!
    
    WICHTIG: Deine Antwort MUSS exakt dieses Format haben:
    PUNKTZAHL|KURZE_BEGRÜNDUNG
    Beispiel: 80|Sehr gut, aber du hast den Ablativus Absolutus am Ende falsch ins Deutsche übertragen."""
    
    try:
        # HIER GEÄNDERT: Korrekter Modell-Name "gemini-1.5-flash"
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        ergebnis = response.text.strip()
        if "|" in ergebnis:
            teile = ergebnis.split("|")
            punkte = int(teile[0].strip())
            feedback = teile[1].strip() if len(teile) > 1 else "Kein Feedback."
        else:
            punkte = 70
            feedback = ergebnis
        return punkte, feedback
    except Exception:
        return -1, "⏳ Das Korrekturbüro prüft die Abgaben nacheinander. Bitte klicke in 5 Sekunden erneut auf 'Satz automatisch von KI überprüfen lassen'."


# ---- 4. DATENBANK & BERECHNUNGEN ----
def lade_daten():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)
        except Exception:
            pass
    return pd.DataFrame(columns=["Name", "Satz_ID", "Dauer", "Uebersetzungs_Punkte", "Hilfe_Stufe1", "Hilfe_KI", "Fertig"])

def speichere_daten(name, satz_id, dauer, uebersetzungs_punkte, h1, h_ki, fertig=False):
    df = lade_daten()
    df = df[~((df["Name"] == name) & (df["Satz_ID"] == satz_id))]
    neuer_eintrag = pd.DataFrame([{
        "Name": name, "Satz_ID": satz_id, "Dauer": dauer, 
        "Uebersetzungs_Punkte": uebersetzungs_punkte,
        "Hilfe_Stufe1": h1, "Hilfe_KI": h_ki, "Fertig": fertig
    }])
    df = pd.concat([df, neuer_eintrag], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

def kicke_team(name):
    df = lade_daten()
    df = df[df["Name"] != name]
    df.to_csv(DB_FILE, index=False)

def berechne_rangliste():
    df = lade_daten()
    fertige_schueler = df[df["Fertig"] == True]
    if fertige_schueler.empty:
        return pd.DataFrame()
    
    scores = fertige_schueler.groupby("Name").agg(
        Gesamt_Dauer=("Dauer", "sum"),
        Gesamt_Qualitaet=("Uebersetzungs_Punkte", "sum"),
        Gesamt_H1=("Hilfe_Stufe1", "sum"),
        Gesamt_KI=("Hilfe_KI", "sum")
    ).reset_index()
    
    min_zeit = scores["Gesamt_Dauer"].min()
    max_zeit = scores["Gesamt_Dauer"].max()
    
    zeit_punkte = []
    for dauer in scores["Gesamt_Dauer"]:
        if max_zeit == min_zeit:
            zeit_punkte.append(300)
        else:
            punkte = 300 * (max_zeit - dauer) / (max_zeit - min_zeit)
            zeit_punkte.append(int(punkte))
            
    scores["Zeit_Punkte"] = zeit_punkte
    scores["Punkte"] = scores["Gesamt_Qualitaet"] + scores["Zeit_Punkte"] - (scores["Gesamt_H1"] * 25) - (scores["Gesamt_KI"] * 50)
    scores["Punkte"] = scores["Punkte"].apply(lambda x: max(0, int(x)))
    
    return scores.sort_values(by="Punkte", ascending=False).reset_index(drop=True)


# ---- 5. BENUTZEROBERFLÄCHE (STREAMLIT) ----
st.set_page_config(page_title="Plinius - GFS Quiz", layout="wide")

gespeicherter_key = lade_api_key()
ki_client = initialisiere_ki(gespeicherter_key) if gespeicherter_key else None

with st.sidebar:
    st.header("⚙️ Lehrer-Bereich")
    admin_passwort = st.text_input("Admin-Passwort", type="password")
    ist_admin = (admin_passwort == "admin123")
    
    if ist_admin:
        st.success("Admin-Modus active!")
        if gespeicherter_key:
            st.info("🔑 API-Key erfolgreich aus Secrets geladen.")
        else:
            st.error("❌ Kein API-Key in den Streamlit Secrets gefunden!")

if ist_admin:
    st.title("🌋 LIVE-RANGLISTE & CONTROL PANEL")
    
    col_refresh, col_kick = st.columns([2, 1])
    
    with col_refresh:
        if st.button("🔄 Rangliste aktualisieren"):
            st.rerun()
            
    df_aktuell = lade_daten()
    if not df_aktuell.empty:
        alle_teams = df_aktuell["Name"].unique()
        with col_kick:
            st.subheader("🗑️ Team kicken / zurücksetzen")
            team_zu_kicken = st.selectbox("Wähle ein Team:", options=alle_teams)
            if st.button("🔴 Team unwiderruflich kicken"):
                kicke_team(team_zu_kicken)
                st.success(f"Team '{team_zu_kicken}' wurde erfolgreich entfernt!")
                time.sleep(1)
                st.rerun()

    rangliste = berechne_rangliste()
    if rangliste.empty:
        st.warning("Es hat noch kein Team das Quiz komplett beendet.")
    else:
        col1, col2, col3 = st.columns(3)
        if len(rangliste) >= 1: col1.metric("🥇 Platz 1", rangliste.iloc[0]["Name"], f"{rangliste.iloc[0]['Punkte']} Pkt")
        if len(rangliste) >= 2: col2.metric("🥈 Platz 2", rangliste.iloc[1]["Name"], f"{rangliste.iloc[1]['Punkte']} Pkt")
        if len(rangliste) >= 3: col3.metric("🥉 Platz 3", rangliste.iloc[2]["Name"], f"{rangliste.iloc[2]['Punkte']} Pkt")
            
        st.write("---")
        rangliste_anzeige = rangliste.copy()
        rangliste_anzeige["Zeit (Minuten)"] = (rangliste_anzeige["Gesamt_Dauer"] / 60).round(1)
        st.dataframe(rangliste_anzeige[["Name", "Gesamt_Qualitaet", "Zeit (Minuten)", "Gesamt_H1", "Gesamt_KI", "Punkte"]], use_container_width=True)

else:
    st.title("📜 Übersetzungs-Challenge: Plinius & der Vesuv")
    
    if "schueler_name" not in st.session_state:
        name_input = st.text_input("Dein Team-Name:")
        if st.button("Quiz starten 🚀") and name_input.strip() != "":
            st.session_state.schueler_name = name_input.strip()
            st.session_state.aktueller_satz = 0
            st.session_state.start_zeit = time.time()
            st.session_state.h1_zaehler = 0
            st.session_state.ki_zaehler = 0
            st.session_state.gesammelte_qualitaet = 0
            st.session_state.h1_freigeschaltet = set()
            st.session_state.letzte_bewertung = None
            if "ki_fragen_pro_satz" not in st.session_state:
                st.session_state.ki_fragen_pro_satz = {}
            st.rerun()
                
    else:
        df_validierung = lade_daten()
        if not df_validierung.empty and st.session_state.schueler_name not in df_validierung["Name"].values and st.session_state.aktueller_satz > 0:
            st.error("Dein Team wurde vom Administrator zurückgesetzt oder entfernt.")
            if st.button("Zurück zum Hauptmenü"):
                del st.session_state.schueler_name
                st.rerun()
            st.stop()

        satz_idx = st.session_state.aktueller_satz
        if satz_idx >= len(SAETZE):
            if "end_zeit" not in st.session_state:
                st.session_state.end_zeit = time.time()
                dauer = st.session_state.end_zeit - st.session_state.start_zeit
                speichere_daten(
                    st.session_state.schueler_name, 999, dauer, 
                    st.session_state.gesammelte_qualitaet, 
                    st.session_state.h1_zaehler, st.session_state.ki_zaehler, True
                )
                st.balloons()
            st.success("🎉 Geschafft! Schau an die Tafel für euer Teamergebnis!")
        else:
            aktuelle_daten = SAETZE[satz_idx]
            st.progress((satz_idx) / len(SAETZE))
            st.subheader(f"Abschnitt {satz_idx + 1} von {len(SAETZE)}")
            
            st.info(f"**Latein:** {aktuelle_daten['latein']}")
            
            if satz_idx == 1: 
                st.markdown("""
                💡 **Gratis-Tipp (Kostenlos):** Das Wort **'kal.'** beendet hier keinen Satz! Es ist das römische Abkürzungszeichen für **'Kalendas'** (von *Kalendae*), was im römischen Kalender den jeweils **ersten Tag eines Monats** bezeichnet. 
                
                *Der Clou:* Da die Römer rückwärts gezählen haben, bedeutet *'Nonum kal. Septembres'* wörtlich 'der neunte Tag vor dem 1. September' (wobei sie den Start- und Endtag mitzählen). Wenn du im Kalender 9 Tage vom 1. September zurückgehst, landest du genau beim geschichtsträchtigen **24. August**!
                """)
            
            uebersetzung = st.text_area("Deine Übersetzung:", height=100, key=f"uebersetzung_{satz_idx}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("### 💡 Stufe 1: Hilfestellungen")
                hilfe_aktiviert = st.checkbox("Vokabeln & Grammatik für diesen Satz freischalten (-25 Pkt)", key=f"h1_check_{satz_idx}")
                if hilfe_aktiviert:
                    if satz_idx not in st.session_state.h1_freigeschaltet:
                        st.session_state.h1_zaehler += 1
                        st.session_state.h1_freigeschaltet.add(satz_idx)
                    
                    st.write("**Vokabeln (schön geordnet):**")
                    for zeile in aktuelle_daten['vokabeln'].split('\n'):
                        if zeile.strip():
                            st.markdown(f"- {zeile.strip()}")
                            
                    st.write("**Grammatik-Analyse:**")
                    for zeile in aktuelle_daten['grammatik'].split('\n'):
                        if zeile.strip():
                            st.markdown(zeile.strip())
                        
            with col2:
                st.write("### 🤖 Stufe 2: KI-Lehrer fragen")
                if not ki_client:
                    st.error("Der Lehrer hat den API-Schlüssel noch nicht hinterlegt.")
                else:
                    aktuelle_fragen = st.session_state.ki_fragen_pro_satz.get(satz_idx, 0)
                    st.write(f"Verbleibende KI-Nachfragen für diesen Satz: **{max(0, 2 - aktuelle_fragen)} von 2**")
                    
                    if aktuelle_fragen >= 2:
                        st.warning("⚠️ Ihr habt eure 2 Fragen für diesen Satz bereits aufgebraucht! Diskutiert im Team oder nutzt die Stufe 1.")
                    else:
                        ki_frage = st.text_input("Deine Frage zur Grammatik/Übersetzung:", key=f"ki_{satz_idx}")
                        if st.button("Fragen (-50 Pkt)", key=f"kibtn_{satz_idx}"):
                            if ki_frage.strip() == "":
                                st.warning("Bitte gib zuerst eine Frage ein!")
                            else:
                                st.session_state.ki_zaehler += 1
                                st.session_state.ki_fragen_pro_satz[satz_idx] = aktuelle_fragen + 1
                                with st.spinner("KI analysiert..."):
                                    antwort = frage_ki_assistent(ki_client, ki_frage, aktuelle_daten)
                                st.session_state[f"ki_antwort_{satz_idx}"] = antwort
                                st.rerun()
                    
                    if f"ki_antwort_{satz_idx}" in st.session_state:
                        st.info(f"**KI-Lehrer:** {st.session_state[f'ki_antwort_{satz_idx}']}")
            
            st.write("---")
            if st.button("Satz automatisch von KI überprüfen lassen 🤖✅", key=f"check_btn_{satz_idx}"):
                if not ki_client:
                    st.error("Fehler: API-Key fehlt. Sag deinem Lehrer Bescheid!")
                elif uebersetzung.strip() == "":
                    st.warning("Bitte gib zuerst eine Übersetzung ein!")
                else:
                    with st.spinner("Eure Übersetzung wird bewertet..."):
                        punkte, feedback = bewerte_uebersetzung(ki_client, uebersetzung, aktuelle_daten)
                        st.session_state.letzte_bewertung = {"punkte": punkte, "feedback": feedback}
            
            if st.session_state.letzte_bewertung is not None:
                punkte = st.session_state.letzte_bewertung["punkte"]
                feedback = st.session_state.letzte_bewertung["feedback"]
                
                if punkte == -1:
                    st.warning(feedback)
                else:
                    st.write(f"### KI-Bewertung: {punkte}/100 Punkten")
                    st.write(f"**Feedback:** {feedback}")
                    
                    if punkte >= 70:
                        st.success("Tolle Leistung! Das reicht, um weiterzukommen.")
                        if st.button("Weiter zum nächsten Satz ➡️", key=f"next_btn_{satz_idx}"):
                            st.session_state.gesammelte_qualitaet += punkte
                            st.session_state.letzte_bewertung = None  
                            st.session_state.aktueller_satz += 1
                            st.rerun()
                    else:
                        st.error("Das ist leider noch nicht nah genug an der korrekten Bedeutung. Versucht es zu verbessern oder nutzt die Hilfestellungen!")