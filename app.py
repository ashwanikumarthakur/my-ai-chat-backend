# app.py - आपका AI चैट बैकएंड

import os
import requests
# [NEW - IMAGE FEATURE START] - (इमेज को टेक्स्ट में बदलने के लिए यह लाइन जोड़ी है)
import base64 
# [NEW - IMAGE FEATURE END]
from flask import Flask, request, jsonify
from flask_cors import CORS

# फ्लास्क एप्लीकेशन बनाएं
app = Flask(__name__)

# CORS सेटअप करें ताकि आपका चैट फ्रंटएंड इससे बात कर सके
# यहाँ आपको अपने फ्रंटएंड का URL डालना होगा
CORS(app, resources={r"/api/*": {"origins": "YOUR_FRONTEND_GITHUB_PAGES_URL"}}) 

# Groq API Key को Render के Environment Variables से प्राप्त करें
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# [NEW - IMAGE FEATURE START] - (इमेज जनरेशन की सेटिंग्स यहाँ जोड़ी हैं)
# आपको Render में 'HF_API_KEY' नाम से अपनी Hugging Face Token डालनी होगी
HF_API_KEY = os.environ.get('HF_API_KEY')
# हम Stable Diffusion XL मॉडल का उपयोग करेंगे
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
# [NEW - IMAGE FEATURE END]

# --- आपका मुख्य AI API रूट ---
@app.route('/api/chat', methods=['POST'])
def chat():
    # उपयोगकर्ता का सवाल JSON से निकालें
    user_data = request.get_json()
    user_prompt = user_data.get('prompt')

    if not user_prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    if not GROQ_API_KEY:
        return jsonify({"error": "API key is not configured on the server"}), 500

    # Groq API को भेजने के लिए पेलोड तैयार करें
    payload = {
        "model": "llama3-8b-8192", # Llama 3 का 8B मॉडल
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Provide concise and accurate answers."
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Groq सर्वर पर रिक्वेस्ट भेजें
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status() # अगर कोई एरर है तो उसे पकड़ें
        
        # AI का जवाब निकालें और फ्रंटएंड को भेजें
        ai_response = response.json()['choices'][0]['message']['content']
        return jsonify({"reply": ai_response})

    except requests.exceptions.RequestException as e:
        print(f"Error calling Groq API: {e}")
        return jsonify({"error": "Failed to get a response from the AI model."}), 500

# [NEW - IMAGE FEATURE START] - (इमेज जनरेशन का पूरा नया फंक्शन यहाँ जोड़ा है)
@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    user_data = request.get_json()
    prompt = user_data.get('prompt')

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    # चेक करें कि Hugging Face Key है या नहीं
    if not HF_API_KEY:
        return jsonify({"error": "Hugging Face API key is missing on server"}), 500

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    try:
        # Hugging Face API को कॉल करें (इमेज बनाने के लिए)
        response = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt})
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to generate image"}), 500

        # Hugging Face बाइनरी डेटा (bytes) देता है, हम उसे Base64 स्ट्रिंग में बदलेंगे
        # ताकि फ्रंटएंड उसे आसानी से दिखा सके (बिना सेव किये)
        image_bytes = response.content
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # यह URL जैसा टेक्स्ट फ्रंटएंड पर इमेज दिखाएगा
        final_image_url = f"data:image/jpeg;base64,{image_base64}"

        return jsonify({"imageUrl": final_image_url})

    except Exception as e:
        print(f"Error generating image: {e}")
        return jsonify({"error": str(e)}), 500
# [NEW - IMAGE FEATURE END]

# --- सर्वर को चालू करें ---
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
