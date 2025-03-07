from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
from google import genai
from PIL import Image as PILImage
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit
app.secret_key = 'your_secret_key'  # Required for session management

# Initialize Gemini client
client = genai.Client(api_key="AIzaSyDjhMXkOZvtIEnjF6jo56cdxmOM11xxYO0")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            
            # Analyze with Gemini
            img = PILImage.open(save_path)
            prompt = (
                """Explain the image"""
            )
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt, img]
            )
            
            analysis = response.text.lower()
            
            if "planting" in analysis or "person planting" in analysis:
                result_text = f"✅ The image contains a person planting a plant. You have earned 20 points."
                # Update reward points in session
                if 'reward_points' not in session:
                    session['reward_points'] = 0
                session['reward_points'] += 20
            else:
                result_text = f"❌ The image does not show someone planting a plant."
            
            return render_template('result.html', filename=filename, analysis=result_text, reward_points=session.get('reward_points', 0))
    
    return render_template('upload.html', reward_points=session.get('reward_points', 0))

@app.route('/ecommerce.html')
def ecommerce():
    return render_template('ecommerce.html', reward_points=session.get('reward_points', 0))

@app.route('/get-reward-points')
def get_reward_points():
    return jsonify({'reward_points': session.get('reward_points', 0)})

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)