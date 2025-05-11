import streamlit as st
from google import generativeai as genai
from gtts import gTTS
import base64
import io

# Configure Gemini
genai.configure(api_key="AIzaSyDjhMXkOZvtIEnjF6jo56cdxmOM11xxYO0")

# Set up Streamlit app
st.set_page_config(page_title="🧠 Gemini Image Analyzer", layout="centered")
st.title("🧠 Gemini Image Analyzer")
st.markdown("""
Upload an image and let **Gemini** identify and analyze the monument in-depth.
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

    if st.button("🔍 Analyze Monument"):
        with st.spinner("Analyzing the monument..."):
            try:
                image_bytes = uploaded_file.getvalue()

                # Define prompt
                prompt = """**Monument Analysis Request**
Identify and analyze the historical monument in this image. Provide a detailed report including:

1. **Official Identification**
   - Official name (original language + English translation)
   - Alternative names/aliases
   - UNESCO World Heritage status (if applicable)

2. **Geographical Context** 🌍
   - Exact geographical coordinates
   - Modern country and region
   - Historical territory name during construction

3. **Historical Timeline** 🕰️
   - Construction start/end dates
   - Original purpose/function
   - Key historical events associated
   - Major renovations/restorations

4. **Architectural Analysis** 🏛️
   - Architectural style/movement
   - Construction materials/methods
   - Notable design features
   - Engineering innovations

5. **Cultural Significance** 📜
   - Religious/political/cultural importance
   - Associated historical figures
   - Modern-day usage/ceremonies

6. **Preservation Status** 🔍
   - Current condition
   - Conservation efforts
   - Public access information

7. **Interesting Facts** 💡
   - 3-5 lesser-known facts
   - Local legends/myths
   - Pop culture references

**Formatting Requirements:**
- Use markdown with headings (##, ###)
- Include relevant emojis in section headers
- Use bullet points for lists
- Highlight key dates in **bold**
- Provide metric and imperial measurements where applicable
- Cite 1-2 reputable historical sources

**Tone:** Academic yet accessible, suitable for educated tourists"""

                # Generate response
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content([
                    {"mime_type": uploaded_file.type, "data": image_bytes},
                    prompt
                ])

                # Show response
                st.success("✅ Monument Identified and Analyzed!")
                st.markdown("### 📝 Analysis Report")
                analysis_text = response.text if response.text else "_No response generated._"
                st.markdown(analysis_text)

                # Text-to-Speech Conversion
                with st.spinner("🔊 Generating audio narration..."):
                    try:
                        tts = gTTS(
                            text=analysis_text,
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
