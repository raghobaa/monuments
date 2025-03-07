import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
import io
import base64
from pydub import AudioSegment
from config import API_KEY

# Configure Gemini AI
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    system_instruction="""You are an expert air quality assistant. Only answer questions about:
    - AQI calculations and interpretations
    - Pollution sources and health impacts
    - Air quality management strategies
    - Environmental regulations
    - Sensor technologies
    Politely decline other topics. Use markdown for technical terms."""
)

# Initialize recognizer
recognizer = sr.Recognizer()

# Streamlit UI Setup
st.set_page_config(page_title="Air Quality Voice Assistant", layout="wide")
st.title("🌍 Air Quality Voice Assistant")

# Session state initialization
if "history" not in st.session_state:
    st.session_state.history = []
if "recording" not in st.session_state:
    st.session_state.recording = False

# Audio processing functions
def voice_to_text(audio_bytes):
    try:
        with io.BytesIO(audio_bytes) as audio_file:
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
                return recognizer.recognize_google(audio)
    except Exception as e:
        st.error(f"Audio processing error: {str(e)}")
        return None

def text_to_speech(text, language):
    tts = gTTS(text=text, lang=language)
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    return audio_bytes.getvalue()

# Main interface columns
input_col, audio_col = st.columns([3, 1])

with input_col:
    user_input = st.text_input("Ask about air quality:", key="text_input")

with audio_col:
    audio_file = st.file_uploader("🎤 Upload voice note", type=["wav", "mp3"])

# Process inputs
if st.button("Submit") or user_input or audio_file:
    input_text = ""
    
    if audio_file:
        audio_bytes = audio_file.read()
        with st.spinner("Processing audio..."):
            input_text = voice_to_text(audio_bytes)
            if input_text:
                st.session_state.history.append(("👤 You (Voice)", input_text))

    if user_input:
        st.session_state.history.append(("👤 You (Text)", user_input))
        input_text = user_input

    if input_text:
        with st.spinner("Analyzing air quality question..."):
            try:
                response = model.generate_content(input_text)
                if response.text:
                    # Format response
                    formatted = response.text.replace("**", "").replace("*", "• ")
                    
                    # Add to history
                    st.session_state.history.append(("🤖 AQI Bot", formatted))
                    
                    # Generate audio
                    audio_bytes = text_to_speech(formatted, "en")
                    st.audio(audio_bytes, format="audio/mp3")
                    
            except Exception as e:
                st.error(f"AI Error: {str(e)}")

# Display chat history
st.subheader("Conversation History")
for sender, message in st.session_state.history[-5:]:  # Show last 5 messages
    with st.expander(sender):
        st.markdown(message)

# Sidebar instructions
st.sidebar.markdown("""
**Voice Command Guide:**
1. Click microphone icon
2. Speak clearly about:
   - AQI values
   - Pollution sources
   - Health recommendations
   - Sensor data
3. Wait for audio analysis

**Supported Topics:**
- PM2.5/PM10 levels
- Ozone alerts
- Clean air strategies
- Air quality regulations
- Sensor technologies
""")

st.sidebar.button("Clear History", on_click=lambda: st.session_state.history.clear())
