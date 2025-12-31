import os
import base64
# [OLD] import requests (Groq ke liye tha, ab zaroorat nahi)
from flask import Flask, request, jsonify
from flask_cors import CORS

# [NEW - GEMINI LIBRARY]
from google import genai
from google.genai import types

app = Flask(__name__)

# CORS Setup
# CORS(app, resources={r"/api/*": {"origins": "YOUR_FRONTEND_URL"}})
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ==============================================================================
# [OLD - GROQ API SETUP] (Commented Out)
# GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
# GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# ==============================================================================

# ==============================================================================
# [NEW - GOOGLE GEMINI SETUP] (Active)
# Render Environment Variables me 'GOOGLE_API_KEY' add karein
# ==============================================================================
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

# Client ko initialize karein (agar key nahi mili to error dega)
if GOOGLE_API_KEY:
    client = genai.Client(api_key=GOOGLE_API_KEY)
else:
    print("Warning: GOOGLE_API_KEY not found in environment variables")
    client = None

# --- CHAT ROUTE ---
@app.route('/api/chat', methods=['POST'])
def chat():
    user_data = request.get_json()
    user_prompt = user_data.get('prompt')

    if not user_prompt:
        return jsonify({"error": "Prompt is required"}), 400

    # [NEW - GEMINI CHAT LOGIC START]
    if not client:
        return jsonify({"error": "Google API Key missing"}), 500

    try:
        # Gemini 2.0 Flash (Fastest Text Model)
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=user_prompt
        )
        return jsonify({"reply": response.text})

    except Exception as e:
        print(f"Gemini Chat Error: {e}")
        return jsonify({"error": str(e)}), 500
    # [NEW - GEMINI CHAT LOGIC END]

    # ==========================================================================
    # [OLD - GROQ CHAT LOGIC] (Disabled/Commented)
    # if not GROQ_API_KEY: return jsonify({"error": "API key missing"}), 500
    # payload = {
    #    "model": "llama3-8b-8192",
    #    "messages": [{"role": "user", "content": user_prompt}]
    # }
    # headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    # try:
    #    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    #    ai_response = response.json()['choices'][0]['message']['content']
    #    return jsonify({"reply": ai_response})
    # except Exception as e:
    #    return jsonify({"error": str(e)}), 500
    # ==========================================================================


# --- IMAGE GENERATION ROUTE ---
@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    user_data = request.get_json()
    prompt = user_data.get('prompt')

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    # [NEW - GEMINI IMAGE LOGIC START]
    if not client:
        return jsonify({"error": "Google API Key missing"}), 500

    try:
        # Imagen 3 (Nano Banana) Model
        response = client.models.generate_image(
            model='imagen-3.0-generate-001',
            prompt=prompt,
            config=types.GenerateImageConfig(
                number_of_images=1,
            )
        )

        # Google API direct bytes deta hai, humein Base64 banana padega
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            final_image_url = f"data:image/jpeg;base64,{image_base64}"
            return jsonify({"imageUrl": final_image_url})
        else:
            return jsonify({"error": "No image generated"}), 500

    except Exception as e:
        print(f"Gemini Image Error: {e}")
        return jsonify({"error": f"Image generation failed: {str(e)}"}), 500
    # [NEW - GEMINI IMAGE LOGIC END]

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
