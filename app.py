import streamlit as st
import google.generativeai as genai
import time

# 1. Konfiguration der Webseite
st.set_page_config(
    page_title="Latein-Trainer mit KI", 
    page_icon="🏛️", 
    layout="centered"
)

st.title("🏛️ Dein persönlicher Latein-Trainer")
st.write("Übersetze die Sätze und frage den KI-Lehrer um Rat, ohne dass er dir direkt die fertige Lösung verrät!")

# 2. API-Key und KI-Modell initialisieren
# Holt sich den Key sicher aus den Streamlit Secrets (unter .streamlit/secrets.toml)
api_key = st.secrets.get("GEMINI_API_KEY")
model = None

if api_key:
    # Kleiner Sicherheitscheck vorab
    if not api_key.startswith("AIzaSy"):
        st.error("⚠️ Hinweis: Dein API-Key in den Secrets beginnt nicht mit 'AIzaSy'. Kostenlose Google AI Studio Keys beginnen eigentlich immer so. Bitte prüfe das noch einmal!")
    
    try:
        genai.configure(api_key=api_key)
        # Wir nutzen 'gemini-1.5-flash', da es absolut stabil läuft
        model = genai.GenerativeModel('gemini-2.0-flash')
    except Exception as e:
        st.error(f"❌ Fehler bei der generellen KI-Einrichtung: {str(e)}")
else:
    st.warning("🔑 Bitte hinterlege deinen `GEMINI_API_KEY` in den Streamlit-Secrets auf der Deploy-Seite oder lokal in deiner `secrets.toml`!")


# 3. Hilfsfunktion für das Rate-Limit
def kontrolliere_rate_limit():
    if "letzter_aufruf" not in st.session_state:
        st.session_state.letzter_aufruf = 0
    jetzt = time.time()
    # Verhindert, dass durch Doppelklicks zu viele Anfragen gleichzeitig gesendet werden
    if jetzt - st.session_state.letzter_aufruf < 2:
        time.sleep(1)
    st.session_state.letzter_aufruf = jetzt


# 4. Die KI-Funktionen mit exakter Fehlerausgabe
def frage_ki_assistent(model, frage, satz_daten):
    if not model:
        return "Fehler: KI nicht verbunden. Hat der Lehrer den API-Key in den Secrets hinterlegt?"
    
    kontrolliere_rate_limit()
    
    prompt = f"""Du bist ein freundlicher, motivierender Lateinlehrer an einer Schule.
    Der Schüler übersetzt gerade diesen Satz: '{satz_daten['latein']}'.
    Die exakten Grammatik-Highlights sind: {satz_daten['grammatik']}.
    Der Schüler fragt dich: '{frage}'
    
    Antworte kurz, verständlich und präzise auf Deutsch. Erkläre die grammatikalische Struktur geduldig, aber verrate NIEMALS das fertige deutsche Satz-Ergebnis!"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Zeigt jetzt den echten Fehler an, statt der Umschreibung!
        return f"❌ KI-Fehler: {str(e)}"


def bewerte_uebersetzung(model, schueler_eingabe, satz_daten):
    if not model:
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
        response = model.generate_content(prompt)
        ergebnis = response.text.strip()
        if "|" in ergebnis:
            teile = ergebnis.split("|")
            punkte = int(teile[0].strip())
            feedback = teile[1].strip() if len(teile) > 1 else "Kein Feedback."
        else:
            punkte = 70
            feedback = ergebnis
        return punkte, feedback
    except Exception as e:
        # Zeigt jetzt den echten Fehler an, statt der Umschreibung!
        return -1, f"❌ Korrektur-Fehler: {str(e)}"


# 5. Beispielsätze (Datenbank)
SAETZE = [
    {
        "id": 1,
        "latein": "Caesar in Galliam properat, ut exercitum duceret.",
        "grammatik": "ut mit Konjunktiv (Finalsatz / Begehrsatz), Richtungsakkusativ (in Galliam)",
        "loesung": "Cäsar eilt nach Gallien, um das Heer zu führen."
    },
    {
        "id": 2,
        "latein": "Magister discipulos laudat, quod diligenter laboraverunt.",
        "grammatik": "Kausalsatz mit quod (weil), Akkusativ-Plural (discipulos)",
        "loesung": "Der Lehrer lobt die Schüler, weil sie fleißig gearbeitet haben."
    },
    {
        "id": 3,
        "latein": "Hannibal alpes cum elephantis transire hercle beschloss.",
        "grammatik": "cum mit Ablativ (Begleitung), Infinitiv-Konstruktion (transire)",
        "loesung": "Hannibal beschloss, die Alpen mit den Elefanten zu überqueren."
    }
]

# 6. Benutzeroberfläche (UI) aufbauen
satz_index = st.selectbox(
    "Wähle einen Übungssatz aus:", 
    range(len(SAETZE)), 
    format_func=lambda x: SAETZE[x]["latein"]
)
aktueller_satz = SAETZE[satz_index]

# Anzeige des aktuellen Satzes
st.info(f"**Lateinischer Satz:**\n### {aktueller_satz['latein']}")

# TAB-Layout für Übersetzung und Fragen
tab1, tab2 = st.tabs(["✍️ Übersetzung einreichen", "💡 KI-Lehrer fragen"])

with tab1:
    st.subheader("Deine Übersetzung prüfen lassen")
    schueler_eingabe = st.text_area("Gib hier deine deutsche Übersetzung ein:", key="eingabe_text")
    
    if st.button("Übersetzung prüfen", type="primary"):
        if not schueler_eingabe:
            st.warning("Bitte gib zuerst eine Übersetzung ein!")
        else:
            with st.spinner("Der Lateinlehrer korrigiert deine Arbeit..."):
                punkte, feedback = bewerte_uebersetzung(model, schueler_eingabe, aktueller_satz)
                
                if punkte == -1:
                    # Hier wird der echte Fehler rot ausgegeben!
                    st.error(feedback)
                else:
                    st.metric(label="Bewertung", value=f"{punkte} / 100 Punkten")
                    if punkte >= 80:
                        st.success(f"🎉 **Sehr gut!** {feedback}")
                    elif punkte >= 50:
                        st.warning(f"👍 **Ganz ordentlich:** {feedback}")
                    else:
                        st.error(f"📉 **Da gibt es noch Fehler:** {feedback}")

with tab2:
    st.subheader("Hilfe vom KI-Lehrer holen")
    st.write("Du hängst fest? Frag nach Vokabeln oder bestimmten Grammatikformen.")
    
    hilfe_frage = st.text_input("Deine Frage an den Lehrer:", placeholder="z.B.: Was ist 'properat' für eine Zeitform?")
    
    if st.button("Lehrer fragen"):
        if not hilfe_frage:
            st.warning("Bitte gib eine Frage ein!")
        else:
            with st.spinner("Der Lehrer überlegt und tippt..."):
                antwort = frage_ki_assistent(model, hilfe_frage, aktueller_satz)
                
                if antwort.startswith("❌"):
                    # Hier wird der echte Fehler rot ausgegeben!
                    st.error(antwort)
                else:
                    st.chat_message("assistant").write(antwort)