import streamlit as st
from google import generativeai as genai
from gtts import gTTS
import base64
import io

# Configure Gemini
genai.configure(api_key="AIzaSyDjhMXkOZvtIEnjF6jo56cdxmOM11xxYO0")

# Set up Streamlit app
st.set_page_config(page_title="🧠 Monument Story Narrator", layout="centered")
st.title("🧠 Monument Story Narrator")
st.markdown("""
Upload an image of a monument, and let **Gemini** narrate its fascinating history and stories.
""")

# Add language selection
language = st.selectbox(
    "🗣️ Select Speech Language",
    options=["English", "Hindi", "Spanish", "French", "Arabic", "Chinese"],
    index=0
)

# Map language names to codes
LANGUAGE_CODES = {
    "English": "en",
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr",
    "Arabic": "ar",
    "Chinese": "zh-CN"
}

# File uploader
uploaded_file = st.file_uploader("📤 Upload a monument image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

    if st.button("🔍 Narrate the Story"):
        with st.spinner("Analyzing the monument and narrating the story..."):
            try:
                image_bytes = uploaded_file.getvalue()

                # Define prompt with storytelling focus
                prompt = """**Monument Story Narration Request**
Identify and narrate the history and stories of the historical monument in this image. Provide an engaging and captivating narrative including:

1. **Historical Context** 🏰
   - Tell the story behind the monument's construction.
   - Include historical events and figures associated with it.
   - Include local legends, myths, or anecdotes tied to the monument.

2. **Cultural Significance** 📜
   - Describe the cultural and political importance of the monument.
   - Include any symbolic meaning or rituals associated with it.
   - Tell how it has influenced the local community or the world.

3. **Unique Stories and Legends** 📖
   - Share lesser-known stories, myths, or local legends about the monument.
   - Highlight interesting or dramatic events that occurred at the site.
   - Tell a compelling narrative that draws in the listener.

**Formatting Requirements:**
- Use narrative-style text, similar to storytelling.
- Use headings for each major section (##, ###).
- Maintain a clear and engaging tone to captivate the listener.

**Tone:** Narrative, engaging, and suitable for a captivating storytelling experience.
"""

                # Generate response
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content([
                    {"mime_type": uploaded_file.type, "data": image_bytes},
                    prompt
                ])

                # Show response
                st.success("✅ Story Generated!")
                st.markdown("### 📝 Monument Story")
                story_text = response.text if response.text else "_No story generated._"
                st.markdown(story_text)

                # Text-to-Speech Conversion
                with st.spinner("🔊 Generating audio narration..."):
                    try:
                        tts = gTTS(
                            text=story_text,
                            lang=LANGUAGE_CODES[language],
                            slow=False
                        )
                        
                        # Save to bytes buffer
                        audio_bytes = io.BytesIO()
                        tts.write_to_fp(audio_bytes)
                        audio_bytes.seek(0)
                        
                        # Autoplay audio using HTML
                        audio_base64 = base64.b64encode(audio_bytes.read()).decode()
                        audio_html = f"""
                            <audio autoplay>
                            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                            </audio>
                        """
                        st.markdown(audio_html, unsafe_allow_html=True)
                        
                    except Exception as tts_error:
                        st.error(f"❌ Audio generation failed: {str(tts_error)}")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
