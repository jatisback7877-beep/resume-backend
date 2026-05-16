from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)  # ye CORS error fix karega

DEEPSEEK_API_KEY = 'sk-a42e2a2625304af7b50288b97c9ca694'   # teri API key
DEEPSEEK_URL = 'https://api.deepseek.com/v1/chat/completions'

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    resume_text = data.get('text', '')
    
    prompt = f"""You are an ATS resume analyzer. Return JSON only:
{{
    "ats_score": 0-100,
    "strengths": ["...","..."],
    "improvements": ["...","..."],
    "skills": ["..."],
    "format_score": 0-10,
    "relevance_score": 0-10,
    "keywords_score": 0-10,
    "ai_message": "..."
}}
Resume: {resume_text[:8000]}"""
    
    headers = {'Authorization': f'Bearer {DEEPSEEK_API_KEY}', 'Content-Type': 'application/json'}
    payload = {'model': 'deepseek-chat', 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0.5}
    
    try:
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        result = resp.json()
        ai_msg = result['choices'][0]['message']['content']
        if ai_msg.startswith('```json'): ai_msg = ai_msg[7:]
        if ai_msg.endswith('```'): ai_msg = ai_msg[:-3]
        return jsonify(json.loads(ai_msg))
    except:
        return jsonify({"error": "AI failed"}), 500

@app.route('/generate-resume', methods=['POST'])
def generate():
    data = request.get_json()
    name = data.get('name', '')
    role = data.get('targetRole', '')
    skills = data.get('skills', '')
    exp = data.get('experience', '')
    
    prompt = f"Write a professional resume for {name}, role {role}, skills {skills}, experience {exp}. Plain text."
    headers = {'Authorization': f'Bearer {DEEPSEEK_API_KEY}', 'Content-Type': 'application/json'}
    payload = {'model': 'deepseek-chat', 'messages': [{'role': 'user', 'content': prompt}]}
    
    try:
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload)
        text = resp.json()['choices'][0]['message']['content']
        return jsonify({"resume": text})
    except:
        return jsonify({"error": "Generation failed"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)