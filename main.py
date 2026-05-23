import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import traceback

app = Flask(__name__)
CORS(app)

MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY', 'YOUR_MISTRAL_API_KEY')
MISTRAL_URL = 'https://api.mistral.ai/v1/chat/completions'

# ---------- HEALTH CHECK ----------
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "message": "Backend is running"
    }), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "alive",
        "endpoints": [
            "/analyze",
            "/generate-resume",
            "/health"
        ]
    }), 200

# ---------- ANALYZE RESUME ----------
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        resume_text = data.get('text', '')

        if not resume_text:
            return jsonify({
                "error": "No text provided"
            }), 400

        prompt = f"""
You are an ATS resume analyzer.

Analyze the resume and return ONLY valid JSON.

Format:
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

Resume:
{resume_text[:8000]}
"""

        headers = {
            'Authorization': f'Bearer {MISTRAL_API_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': 'mistral-small-latest',
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,
            'max_tokens': 2000
        }

        print("Analyzing Resume...")

        resp = requests.post(
            MISTRAL_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        print("Status:", resp.status_code)

        if resp.status_code != 200:
            print(resp.text)
            return jsonify({
                "error": f"Mistral API Error: {resp.status_code}"
            }), 500

        result = resp.json()
        ai_msg = result['choices'][0]['message']['content'].strip()

        # Safely clean JSON markdown
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
        return jsonify({
            "error": str(e)
        }), 500


# ---------- GENERATE RESUME DATA ----------
@app.route('/generate-resume', methods=['POST'])
def generate_resume():
    try:
        data = request.get_json()
        
        template = data.get('template', 'modern')
        name = data.get('name', 'Your Name')
        role = data.get('role', data.get('targetRole', 'Professional'))
        skills = data.get('skills', '')
        experience = data.get('experience', '1-3 years')
        company = data.get('company', '')
        achievements = data.get('achievements', '')
        leadership = data.get('execLeadership', '')

        # AI se hum sirf text content enhance karwayenge
        prompt = f"""You are an expert ATS resume writer and career coach. 
Enhance the candidate's details for a high-quality {template} resume template.
Return ONLY valid JSON format without any markdown blocks.

Candidate Details:
Role: {role}
Experience: {experience}
Skills: {skills}
Company: {company}
Achievements: {achievements}
Leadership (if executive): {leadership}

Format required:
{{
    "summary": "Write a strong 3-4 line professional summary. Make it impactful.",
    "enhanced_skills": "Rewrite and optimize the provided skills as a comma-separated string, adding relevant industry keywords.",
    "experience_bullets": "Write 3-4 highly professional bullet points highlighting achievements and metrics. Return them as a single string separated by commas or semicolons."
}}
"""

        headers = {
            'Authorization': f'Bearer {MISTRAL_API_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': 'mistral-small-latest',
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.4,
            'max_tokens': 1500
        }

        print(f"Generating AI Content for {template} resume...")

        resp = requests.post(
            MISTRAL_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        print("Status:", resp.status_code)

        if resp.status_code != 200:
            print(resp.text)
            return jsonify({
                "error": "AI generation failed"
            }), 500

        result = resp.json()
        ai_msg = result['choices'][0]['message']['content'].strip()

        # Clean JSON markdown blocks
        if ai_msg.startswith('```json'):
            ai_msg = ai_msg[7:]
        if ai_msg.startswith('```'):
            ai_msg = ai_msg[3:]
        if ai_msg.endswith('```'):
            ai_msg = ai_msg[:-3]

        ai_msg = ai_msg.strip()
        resume_data = json.loads(ai_msg)

        # Yeh JSON data ab seedha frontend ko jayega
        return jsonify(resume_data)

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
