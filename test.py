import streamlit as st
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
import re
import urllib.parse
import pytz

# Configure Gemini AI
genai.configure(api_key="AIzaSyDjhMXkOZvtIEnjF6jo56cdxmOM11xxYO0")

# Streamlit setup
st.set_page_config(page_title="Air Quality Hub", layout="wide")
load_dotenv('.env')

# API configuration
API_URL = "https://api.waqi.info/feed/"
API_TOKEN = "4cf1cbc659fd0c7c017efae3c5296ef7d840f3f1"
pla=""

def get_lat_lon(place_name):
    """Get coordinates using Gemini AI with improved parsing"""
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    prompt = f"""Provide ONLY numeric latitude and longitude for {place_name}
    in EXACT format: '12.971599,77.594566' without any text"""
    pla=""
    try:
        response = model.generate_content(prompt)
        coords = re.findall(r"[-+]?\d+\.\d+", response.text)
        
        if len(coords) == 2:
            return float(coords[0]), float(coords[1])
        st.error(f"Failed to get coordinates for: {place_name}")
        return None, None
    except Exception as e:
        st.error(f"Geocoding error: {str(e)}")
        return None, None

def get_aqi_data(search_type, param):
    """Unified API fetcher with proper error handling"""
    try:
        if search_type == "city":
            city_encoded = urllib.parse.quote(param)
            url = f"{API_URL}{city_encoded}/?token={API_TOKEN}"  # Corrected URL structure
        elif search_type == "geo":
            lat, lng = param
            url = f"{API_URL}geo:{lat};{lng}/?token={API_TOKEN}"
        elif search_type == "station":
            url = f"{API_URL}@{param}/?token={API_TOKEN}"
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] != 'ok':
            error_msg = data.get('data', 'Unknown error')
            if "Unknown station" in error_msg:
                st.error(f"City not found: {param}. Use official names from aqicn.org/city")
            else:
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
st.markdown("Triple search mode: City names, landmarks, or station IDs")

# Search Interface
search_mode = st.selectbox(
    "Select search type:",
    ["City Name", "Place Name", "Station ID"],
    index=0,
    help="Choose between official city names, any global landmark, or direct station IDs"
)

data = None
with st.form("search_form"):
    if search_mode == "City Name":
        city_input = st.text_input("Enter official city name", "delhi",
                                 help="Use official names from aqicn.org/city (e.g., 'london', 'beijing')")
        submitted = st.form_submit_button("🌆 Get City Air Quality")
        if submitted:
            if not city_input.strip():
                st.error("Please enter a city name")
            else:
                data = get_aqi_data("city", city_input)
                
    elif search_mode == "Place Name":
        place_input = st.text_input("Enter any location/landmark", "Taj Mahal",
                                  help="Try addresses, tourist spots, or geographic features")
        submitted = st.form_submit_button("🗺️ Locate & Analyze")
        if submitted:
            lat, lon = get_lat_lon(place_input)
            if lat and lon:
                data = get_aqi_data("geo", (lat, lon))
                
    elif search_mode == "Station ID":
        station_input = st.text_input("Station ID", "3758",
                                    help="Find IDs at waqi.info/map (e.g., '1437' for Delhi)")
        submitted = st.form_submit_button("📡 Fetch Station Data")
        if submitted:
            data = get_aqi_data("station", station_input)

# Data Visualization
if data:
    # Header Section
    st.subheader(f"{data['city']['name']} Air Quality Report")
    
    # Real-time Metrics
    cols = st.columns(4)
    with cols[0]:
        ts = datetime.fromtimestamp(data['time']['v']).strftime('%b %d, %Y %H:%M')
        st.metric("Last Updated", ts)
    
    with cols[1]:
        aqi = data.get('aqi', 'N/A')
        status = ("Good", "Moderate", "Unhealthy (S)", 
                "Unhealthy", "Very Unhealthy", "Hazardous")[(aqi > 50) + (aqi > 100) + 
                                                          (aqi > 150) + (aqi > 200) + 
                                                          (aqi > 300)]
        st.metric("Air Quality Index", f"{aqi} - {status}")
    
    with cols[2]:
        dom = data.get('dominentpol', 'N/A').upper()
        st.metric("Main Pollutant", dom, help="Primary harmful substance in air")
    
    with cols[3]:
        src = data['attributions'][0]['name'] if data['attributions'] else 'Unknown'
        st.metric("Data Source", src)

    # Detailed Pollution Breakdown
    st.subheader("🧪 Pollutant Concentration Analysis")
    pollutants = {
        'pm25': {'name': 'PM₂.₅', 'unit': 'µg/m³', 'safe': 15, 'src': 'Vehicles, Industry'},
        'pm10': {'name': 'PM₁₀', 'unit': 'µg/m³', 'safe': 45, 'src': 'Dust, Construction'},
        'o3': {'name': 'Ozone', 'unit': 'µg/m³', 'safe': 100, 'src': 'Sunlight Reactions'},
        'no2': {'name': 'NO₂', 'unit': 'µg/m³', 'safe': 40, 'src': 'Combustion'},
        'so2': {'name': 'SO₂', 'unit': 'µg/m³', 'safe': 20, 'src': 'Power Plants'},
        'co': {'name': 'CO', 'unit': 'mg/m³', 'safe': 4, 'src': 'Vehicle Exhaust'}
    }
    
    cols = st.columns(3)
    for idx, (code, info) in enumerate(pollutants.items()):
        with cols[idx % 3]:
            cont = st.container(border=True)
            with cont:
                if code in data.get('iaqi', {}):
                    val = data['iaqi'][code]['v']
                    cont.markdown(f"""
                        **{info['name']}**  
                        🎚️ `{val} {info['unit']}`  
                        ✅ **Safe Limit:** {info['safe']}  
                        📍 **Sources:** {info['src']}
                        """)
                else:
                    cont.markdown(f"**{info['name']}**  \n🚫 No data available")
# Add to existing imports


# Add after get_aqi_data function
def get_weather_analysis(lat, lon):
    """Get weather insights using Gemini AI with proper error handling"""
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    timestamp = datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M %Z')
    
    prompt = f"""
    Analyze weather patterns for coordinates {lat},{lon} using (https://www.accuweather.com) website. 
    Provide  only :
    - Current temperature feel
    - Wind speed impact analysis 
    - Weather pattern anomalies from 
   
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Weather analysis failed: {str(e)}")
        return None

# Modify the data visualization section
if data:
    # Add weather columns
    cols = st.columns(4)
    
    
    with cols[1]:
        aqi = data.get('aqi', 'N/A')
        status = ("Good", "Moderate", "Unhealthy (S)", 
                "Unhealthy", "Very Unhealthy", "Hazardous")[(aqi > 50) + (aqi > 100) + 
                                                          (aqi > 150) + (aqi > 200) + 
                                                          (aqi > 300)]
        st.metric("Air Quality Index", f"{aqi} - {status}")
    
    # Add weather metrics
    with cols[2]:
        if 'iaqi' in data:
            temp = data['iaqi'].get('t', {}).get('v', 'N/A')
            st.metric("Temperature", f"{temp}°C" if temp != 'N/A' else temp)
            
    with cols[3]:
        wind_speed = data['iaqi'].get('ws', {}).get('v', 'N/A')
        wind_dir = data['iaqi'].get('wd', {}).get('v', 'N/A')
        wind_str = f"{wind_speed} km/h" if wind_speed != 'N/A' else 'N/A'
        if wind_dir != 'N/A':
            wind_str += f" ({wind_dir}°)"
        st.metric("Wind Speed/Direction", wind_str)

    # Add Gemini weather analysis


    # Existing pollution breakdown remains unchanged...







# Informational Sidebar
st.sidebar.markdown("""
    **🔍 Search Guide**
    - **City Name:** Official locations from [aqicn.org/city](https://aqicn.org/city/)
    - **Place Name:** Any global location using AI geocoding  
    - **Station ID:** Direct sensor access (numeric IDs only)
    
    **📊 AQI Interpretation**  
    0-50: Good (Green)  
    51-100: Moderate (Yellow)  
    101-150: Unhealthy Sensitive (Orange)  
    151-200: Unhealthy (Red)  
    201-300: Very Unhealthy (Purple)  
    300+: Hazardous (Maroon)
    """)

st.sidebar.info(
  
    """AQI Scale:
🟢 0-50: Good
🟡 51-100: Moderate
🟠 101-150: Unhealthy for Sensitive
🔴 151-200: Unhealthy
🟣 201-300: Very Unhealthy
⚫ 300+: Hazardous""")
