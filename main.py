import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import traceback

app = Flask(__name__)
CORS(app)

# Mistral API configuration
MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY', 'pB8Te7q8wrBt1qEBGBTgTMDFhEQQOkQC')
MISTRAL_URL = 'https://api.mistral.ai/v1/chat/completions'

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        resume_text = data.get('text', '')
        if not resume_text:
            return jsonify({"error": "No text provided"}), 400

        prompt = f"""You are an ATS resume analyzer. Analyze the resume and return ONLY valid JSON (no extra text). Format:
{{
    "ats_score": integer 0-100,
    "strengths": ["strength1", "strength2", "strength3"],
    "improvements": ["improvement1", "improvement2", "improvement3"],
    "skills": ["skill1", "skill2"],
    "format_score": 0-10,
    "relevance_score": 0-10,
    "keywords_score": 0-10,
    "ai_message": "short summary"
}}

Resume text:
{resume_text[:8000]}"""

        headers = {
            'Authorization': f'Bearer {MISTRAL_API_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'mistral-small-latest',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.3,
            'max_tokens': 2000
        }

        print("Calling Mistral API for analysis...")
        resp = requests.post(MISTRAL_URL, headers=headers, json=payload, timeout=60)
        print(f"Mistral response status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"Mistral error: {resp.text}")
            return jsonify({"error": f"Mistral API error: {resp.status_code}"}), 500
            
        result = resp.json()
        ai_msg = result['choices'][0]['message']['content'].strip()
        
        # Clean JSON
        if ai_msg.startswith('```json'):
            ai_msg = ai_msg[7:]
        if ai_msg.startswith('```'):
            ai_msg = ai_msg[3:]
        if ai_msg.endswith('```'):
            ai_msg = ai_msg[:-3]
        ai_msg = ai_msg.strip()
        
        analysis = json.loads(ai_msg)
        return jsonify(analysis)
        
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route('/generate-resume', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        name = data.get('name', 'Your Name')
        role = data.get('targetRole', 'Professional')
        skills = data.get('skills', 'Communication, Problem Solving')
        exp = data.get('experience', '1-3 years')
        
        prompt = f"""Write a professional, ATS-friendly resume for:
Name: {name}
Target Role: {role}
Skills: {skills}
Experience: {exp}

Include sections: Contact Info, Professional Summary, Skills, Work Experience (2-3 bullet points as placeholders), Education. Return plain text without markdown."""
        
        headers = {
            'Authorization': f'Bearer {MISTRAL_API_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'mistral-small-latest',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.5,
            'max_tokens': 2000
        }
        
        print("Calling Mistral API for resume generation...")
        resp = requests.post(MISTRAL_URL, headers=headers, json=payload, timeout=60)
        print(f"Mistral response status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"Mistral error: {resp.text}")
            return jsonify({"error": f"Mistral API error: {resp.status_code}"}), 500
            
        result = resp.json()
        resume_text = result['choices'][0]['message']['content']
        return jsonify({"resume": resume_text})
        
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
