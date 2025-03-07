import streamlit as st
from gtts import gTTS
import os
import tempfile
import base64
import re
import google.generativeai as genai
from streamlit_mic_recorder import speech_to_text
from langdetect import detect
import streamlit.components.v1 as components

# Browser permissions for audio
components.html("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    window.AudioContext = window.AudioContext || window.webkitAudioContext;
    navigator.mediaDevices.getUserMedia({ audio: true });
});
</script>
""")


st.title("Speech to Speech :red[Assistant]")

# Configure API (using Streamlit secrets)
client = genai.configure(api_key="ea768302bd86e0690c74f1bf87dcb697212d28c3" )

# Model configuration
instruction = """You are a helpful multilingual assistant. Follow these rules:
1. Respond in the same language as the question
2. Keep answers under 200 characters
3. Avoid markdown formatting
4. Prioritize clarity over complexity"""
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    generation_config={
        "temperature": 0.2,
        "max_output_tokens": 200,
        "response_mime_type": "text/plain"
    },
    system_instruction=instruction
)

def text_to_speech(text, lang='en'):
    """Convert text to speech with safe temp file handling"""
    with tempfile.NamedTemporaryFile(delete=True, suffix='.mp3') as fp:
        try:
            tts = gTTS(text=text, lang=lang, tld="co.in", slow=False)
            tts.save(fp.name)
            return fp.name
        except Exception as e:
            st.error(f"TTS Error: {str(e)}")
            return None

def get_audio_player(file_path):
    """Create HTML5 audio player with base64 encoded audio"""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            return f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
    except Exception as e:
        st.error(f"Audio Error: {str(e)}")
        return None

# Initialize chat session
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# Speech input
with st.spinner("Converting speech to text..."):
    text = speech_to_text(language="en", just_once=True, key="STT")

if text:
    st.chat_message("user").write(text)
    
    with st.chat_message("assistant"):
        try:
            # Generate response
            response = st.session_state.chat.send_message(text)
            
            # Clean response text
            clean_text = re.sub(r'[^\w\s.,!?\'"-]', '', response.text)
            st.write(clean_text)
            
            # Detect language for TTS
            try:
                lang = detect(clean_text)
            except:
                lang = 'en'  # Fallback to English
            
            # Generate and play audio
            audio_file = text_to_speech(clean_text, lang=lang)
            if audio_file:
                audio_player = get_audio_player(audio_file)
                if audio_player:
                    st.markdown(audio_player, unsafe_allow_html=True)
                os.remove(audio_file)

        except genai.types.StopCandidateException as e:
            st.error("Response generation stopped unexpectedly")
        except genai.types.BlockedPromptException as e:
            st.error("Query blocked for safety reasons")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
else:
    st.info("Please click 'Start Recording' and speak something!")
