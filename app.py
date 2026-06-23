import streamlit as st
import google.generativeai as genai
import time

# 1. Konfiguration der Webseite
st.set_page_config(
    page_title="Latein-Trainer mit KI", 
    page_icon="🏛️", 
    layout="centered"
)

# Schönes Design für den Header
st.title("🏛️ Dein persönlicher Latein-Trainer")
st.write(
    "Willkommen im interaktiven Latein-Klassenzimmer! Übersetze die Sätze, "
    "lasse deine Arbeit bewerten oder frage den KI-Lehrer um Rat – "
    "er hilft dir geduldig weiter, ohne dir die fertige Lösung vorzusagen."
)
st.markdown("---")

# 2. API-Key und KI-Modell initialisieren
# Holt sich den Key sicher aus den Streamlit Secrets
api_key = st.secrets.get("GEMINI_API_KEY")
model = None

if api_key:
    # Kleiner Vorab-Check für den User
    if not api_key.startswith("AIzaSy"):
        st.error("⚠️ Hinweis: Dein API-Key in den Secrets beginnt nicht mit 'AIzaSy'. Bitte überprüfe deinen Key im Google AI Studio!")
    
    try:
        genai.configure(api_key=api_key)
        # Hier ist jetzt das richtige, aktuelle Modell hinterlegt!
        model = genai.GenerativeModel('gemini-2.0-flash')
    except Exception as e:
        st.error(f"❌ Fehler bei der generellen KI-Einrichtung: {str(e)}")
else:
    st.warning("🔑 Bitte hinterlege deinen `GEMINI_API_KEY` in den Streamlit-Secrets deiner App!")


# 3. Hilfsfunktion für das Rate-Limit (Verhindert Spam-Klicks)
def kontrolliere_rate_limit():
    if "letzter_aufruf" not in st.session_state:
        st.session_state.letzter_aufruf = 0
    jetzt = time.time()
    if jetzt - st.session_state.letzter_aufruf < 2:
        time.sleep(1.5)
    st.session_state.letzter_aufruf = jetzt


# 4. Die KI-Hauptfunktionen
def frage_ki_assistent(model, frage, satz_daten):
    if not model:
        return "Fehler: Die KI ist nicht verbunden. Bitte überprüfe den API-Key."
    
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
        return f"❌ KI-Fehler: {str(e)}"


def bewerte_uebersetzung(model, schueler_eingabe, satz_daten):
    if not model:
        return -1, "Fehler: Die KI ist nicht verbunden."
        
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
            feedback = teile[1].strip() if len(teile) > 1 else "Kein Feedback hinterlassen."
        else:
            punkte = 70
            feedback = ergebnis
        return punkte, feedback
    except Exception as e:
        return -1, f"❌ Korrektur-Fehler: {str(e)}"


# 5. Satz-Datenbank (Hier kannst du beliebig viele Sätze hinzufügen!)
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
    },
    {
        "id": 4,
        "latein": "Amici Statuam magnam in foro vident.",
        "grammatik": "Akkusativ-Objekt (statuam magnam), Lokativ-Ablativ (in foro)",
        "loesung": "Die Freunde sehen eine große Statue auf dem Marktplatz."
    }
]

# 6. Benutzeroberfläche (UI)
st.subheader("🤖 Schritt 1: Wähle deine Aufgabe")
satz_index = st.selectbox(
    "Welchen Satz möchtest du trainieren?", 
    range(len(SAETZE)), 
    format_func=lambda x: f"Satz {SAETZE[x]['id']}: {SAETZE[x]['latein'][:40]}..."
)
aktueller_satz = SAETZE[satz_index]

# Große, gut lesbare Anzeige des aktiven Satzes
st.info(f"**Lateinischer Originalsatz:**\n## {aktueller_satz['latein']}")

# Registerkarten (Tabs) für die Interaktion
tab1, tab2 = st.tabs(["✍️ Übersetzung einreichen", "💡 KI-Lehrer um Hilfe bitten"])

with tab1:
    st.markdown("### Deine Übersetzung prüfen lassen")
    schueler_eingabe = st.text_area(
        "Gib hier deine deutsche Übersetzung ein:", 
        placeholder="z.B.: Cäsar eilt nach Gallien...",
        key="schueler_code_eingabe"
    )
    
    if st.button("Übersetzung prüfen", type="primary", use_container_width=True):
        if not schueler_eingabe:
            st.warning("⚠️ Bitte trage zuerst eine Übersetzung in das Textfeld ein!")
        else:
            with st.spinner("Der Lateinlehrer korrigiert..."):
                punkte, feedback = bewerte_uebersetzung(model, schueler_eingabe, aktueller_satz)
                
                if punkte == -1:
                    st.error(feedback)
                    st.info("💡 *Tipp zum Fehler 429:* Wenn hier das Quota-Limit steht, warte kurz 1 Minute oder erstelle im Google AI Studio einen frischen, neuen API-Key.")
                else:
                    st.markdown("---")
                    st.metric(label="Erreichte Punktzahl", value=f"{punkte} / 100")
                    
                    if punkte >= 85:
                        st.success(f"🎉 **Exzellent!** {feedback}")
                    elif punkte >= 50:
                        st.warning(f"👍 **Guter Versuch:** {feedback}")
                    else:
                        st.error(f"📉 **Schau noch mal genau hin:** {feedback}")

with tab2:
    st.markdown("### Fragen an den KI-Assistenten")
    st.write("Du kommst bei einem Wort oder der Grammatik nicht weiter? Frag den Lehrer!")
    
    hilfe_frage = st.text_input(
        "Deine Frage zum Satz:", 
        placeholder="z.B.: Was ist 'ut' in diesem Satz für eine Konjunktion?",
        key="lehrer_frage_input"
    )
    
    if st.button("Frage absenden", use_container_width=True):
        if not hilfe_frage:
            st.warning("⚠️ Bitte gib zuerst eine Frage ein!")
        else:
            with st.spinner("Der Lehrer überlegt..."):
                antwort = frage_ki_assistent(model, hilfe_frage, aktueller_satz)
                
                if antwort.startswith("❌"):
                    st.error(antwort)
                else:
                    st.markdown("---")
                    st.markdown("**Antwort des Lateinlehrers:**")
                    st.chat_message("assistant").write(antwort)