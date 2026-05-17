import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import traceback

app = Flask(__name__)
CORS(app)  # CORS error fix

# API key – environment variable se le, nahi to direct use kar (fallback)
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-a42e2a2625304af7b50288b97c9ca694')
DEEPSEEK_URL = 'https://api.deepseek.com/v1/chat/completions'

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        resume_text = data.get('text', '')
        if not resume_text:
            return jsonify({"error": "No resume text provided"}), 400

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
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'deepseek-chat',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.3,
            'max_tokens': 2000
        }

        print("Calling DeepSeek API for analysis...")
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60)
        print(f"DeepSeek response status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"DeepSeek error: {resp.text}")
            return jsonify({"error": f"DeepSeek API error: {resp.status_code}"}), 500
            
        result = resp.json()
        ai_msg = result['choices'][0]['message']['content']
        
        # Clean JSON if wrapped in markdown
        ai_msg = ai_msg.strip()
        if ai_msg.startswith('```json'):
            ai_msg = ai_msg[7:]
        if ai_msg.startswith('```'):
            ai_msg = ai_msg[3:]
        if ai_msg.endswith('```'):
            ai_msg = ai_msg[:-3]
        ai_msg = ai_msg.strip()
        
        # Parse JSON
        analysis = json.loads(ai_msg)
        
        # Ensure all required fields exist
        required_fields = ['ats_score', 'strengths', 'improvements', 'skills', 
                          'format_score', 'relevance_score', 'keywords_score', 'ai_message']
        for field in required_fields:
            if field not in analysis:
                analysis[field] = 0 if 'score' in field else []
        
        return jsonify(analysis)
        
    except requests.exceptions.Timeout:
        print("DeepSeek API timeout")
        return jsonify({"error": "AI service timeout, please try again"}), 500
    except requests.exceptions.ConnectionError:
        print("DeepSeek API connection error")
        return jsonify({"error": "Cannot connect to AI service"}), 500
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {ai_msg if 'ai_msg' in locals() else 'N/A'}")
        return jsonify({"error": "AI response format invalid"}), 500
    except Exception as e:
        print("="*50)
        print("ERROR in /analyze:")
        traceback.print_exc()
        print("="*50)
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


@app.route('/generate-resume', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
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
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'deepseek-chat',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.5,
            'max_tokens': 2000
        }

        print("Calling DeepSeek API for resume generation...")
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60)
        print(f"DeepSeek response status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"DeepSeek error: {resp.text}")
            return jsonify({"error": f"DeepSeek API error: {resp.status_code}"}), 500
            
        result = resp.json()
        resume_text = result['choices'][0]['message']['content']
        
        return jsonify({"resume": resume_text})
        
    except requests.exceptions.Timeout:
        print("DeepSeek API timeout")
        return jsonify({"error": "AI service timeout"}), 500
    except Exception as e:
        print("="*50)
        print("ERROR in /generate-resume:")
        traceback.print_exc()
        print("="*50)
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
