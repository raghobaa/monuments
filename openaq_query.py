import streamlit as st
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
import re
import urllib.parse

# Load API keys securely
load_dotenv('.env')
 
AQI_API_TOKEN = os.getenv("AQI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Streamlit setup
st.set_page_config(page_title="Air Quality Hub", layout="wide")

# AQI API Configuration
API_URL = "https://api.waqi.info/feed/"

def get_lat_lon(place_name):
    """Get coordinates using Gemini AI with improved parsing"""
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    prompt = f"""Provide ONLY numeric latitude and longitude for {place_name}
    in EXACT format: '12.971599,77.594566' without any extra text"""
    
    try:
        response = model.generate_content(prompt)
        coords_text = response.text.strip()
        coords = re.findall(r"[-+]?\d+\.\d+", coords_text)

        if len(coords) == 2:
            return float(coords[0]), float(coords[1])
        
        st.error(f"Failed to get coordinates for: {place_name}")
        return None, None
    except Exception as e:
        st.error(f"Geocoding error: {str(e)}")
        return None, None

def get_aqi_data(search_type, param):
    """Fetch air quality data from AQICN API"""
    try:
        if search_type == "city":
            city_encoded = urllib.parse.quote(param)
            url = f"{API_URL}{city_encoded}/?token={AQI_API_TOKEN}"
        elif search_type == "geo":
            lat, lng = param
            url = f"{API_URL}geo:{lat};{lng}/?token={AQI_API_TOKEN}"
        elif search_type == "station":
            url = f"{API_URL}@{param}/?token={AQI_API_TOKEN}"
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data['status'] != 'ok':
            error_msg = data.get('data', 'Unknown error')
            st.error(f"API Error: {error_msg}")
            return None

        return data['data']
    
    except requests.exceptions.RequestException as e:
        st.error(f"Network Error: {str(e)}")
        return None
    except json.JSONDecodeError:
        st.error("Invalid API response format")
        return None

# Streamlit UI Components
st.title("🌐 Smart Air Quality Analyzer")
st.markdown("Search by city names, landmarks, or station IDs")

# Search Interface
search_mode = st.selectbox(
    "Select search type:",
    ["City Name", "Place Name", "Station ID"],
    index=0,
    help="Choose between city names, landmarks, or station IDs"
)

data = None
with st.form("search_form"):
    if search_mode == "City Name":
        city_input = st.text_input("Enter city name", "Delhi")
        submitted = st.form_submit_button("🌆 Get City Air Quality")
        if submitted:
            if not city_input.strip():
                st.error("Please enter a city name")
            else:
                data = get_aqi_data("city", city_input)
                
    elif search_mode == "Place Name":
        place_input = st.text_input("Enter a location/landmark", "Taj Mahal")
        submitted = st.form_submit_button("🗺️ Locate & Analyze")
        if submitted:
            lat, lon = get_lat_lon(place_input)
            if lat and lon:
                data = get_aqi_data("geo", (lat, lon))
                
    elif search_mode == "Station ID":
        station_input = st.text_input("Station ID", "3758")
        submitted = st.form_submit_button("📡 Fetch Station Data")
        if submitted:
            data = get_aqi_data("station", station_input)

# Data Visualization
if data:
    st.subheader(f"{data['city']['name']} Air Quality Report")

    # Real-time Metrics
    cols = st.columns(4)
    with cols[0]:
        ts = datetime.fromtimestamp(data['time']['v']).strftime('%b %d, %Y %H:%M')
        st.metric("Last Updated", ts)
    
    with cols[1]:
        aqi = data.get('aqi', 'N/A')
        AQI_CATEGORIES = [
            (50, "Good"), (100, "Moderate"), (150, "Unhealthy (S)"),
            (200, "Unhealthy"), (300, "Very Unhealthy"), (9999, "Hazardous")
        ]
        status = next(label for threshold, label in AQI_CATEGORIES if aqi <= threshold)
        st.metric("Air Quality Index", f"{aqi} - {status}")
    
    with cols[2]:
        dom = data.get('dominentpol', 'N/A').upper()
        st.metric("Main Pollutant", dom)
    
    with cols[3]:
        src = data['attributions'][0]['name'] if data['attributions'] else 'Unknown'
        st.metric("Data Source", src)

    # Pollutant Breakdown
    st.subheader("🧪 Pollutant Concentration Analysis")
    pollutants = {
        'pm25': ('PM₂.₅', 'µg/m³', 15),
        'pm10': ('PM₁₀', 'µg/m³', 45),
        'o3': ('Ozone', 'µg/m³', 100),
        'no2': ('NO₂', 'µg/m³', 40),
        'so2': ('SO₂', 'µg/m³', 20),
        'co': ('CO', 'mg/m³', 4)
    }

    cols = st.columns(3)
    for idx, (code, (name, unit, safe_limit)) in enumerate(pollutants.items()):
        with cols[idx % 3]:
            val = data['iaqi'].get(code, {}).get('v', "N/A")
            st.markdown(f"**{name}**  \n🎚️ `{val} {unit}`  \n✅ Safe Limit: {safe_limit}")

# AQI Formula Explanation
st.subheader("🧮 AQI Calculation Methodology")
with st.expander("View Formula & Explanation", expanded=True):
    st.markdown(r"""
    **AQI Formula**  
    $$ I_p = \frac{I_{Hi} - I_{Lo}}{BP_{Hi} - BP_{Lo}} \times (C_p - BP_{Lo}) + I_{Lo} $$
    Where:
    - $I_p$ = Pollutant AQI value
    - $C_p$ = Measured concentration
    - $BP_{Hi}/BP_{Lo}$ = Breakpoint range
    - $I_{Hi}/I_{Lo}$ = AQI range
    """)

# Informational Sidebar
st.sidebar.markdown("""
    **🔍 Search Guide**
    - **City Name:** Official names from [aqicn.org/city](https://aqicn.org/city/)
    - **Place Name:** AI-powered geolocation
    - **Station ID:** Direct sensor lookup
    
    **📊 AQI Interpretation**  
    - 🟢 0-50: Good  
    - 🟡 51-100: Moderate  
    - 🟠 101-150: Unhealthy for Sensitive  
    - 🔴 151-200: Unhealthy  
    - 🟣 201-300: Very Unhealthy  
    - ⚫ 300+: Hazardous  
""")
