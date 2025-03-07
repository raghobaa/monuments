import google.generativeai as genai
import re

# Set up Gemini AI with your API key
genai.configure(api_key="AIzaSyDjhMXkOZvtIEnjF6jo56cdxmOM11xxYO0")

def get_lat_lon(place_name):
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    
    # Modified prompt to ensure consistent format
    prompt = f"Provide the exact latitude and longitude for {place_name} in format: latitude:12.971599, longitude:77.594566"
    
    try:
        response = model.generate_content(prompt)
        # Extract numbers using regular expression
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", response.text)
        
        if len(numbers) >= 2:
            lat = float(numbers[0])
            lon = float(numbers[1])
            return lat, lon
        else:
            print("Could not find coordinates in response")
            return None, None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None

# Example usage
place_name = "delhi"
latitude, longitude = get_lat_lon(place_name)

if latitude is not None and longitude is not None:
    print(f"Coordinates of {place_name}:")
    print(f"Latitude: {latitude}")
    print(f"Longitude: {longitude}")
else:
    print("Failed to get coordinates")

