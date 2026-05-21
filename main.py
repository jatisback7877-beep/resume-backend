import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import traceback

app = Flask(__name__)
CORS(app)

MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY', 'pB8Te7q8wrBt1qEBGBTgTMDFhEQQOkQC')
MISTRAL_URL = 'https://api.mistral.ai/v1/chat/completions'

# ---------- HEALTH CHECK ENDPOINT (ADDED) ----------
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Backend is running"}), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "alive", "endpoints": ["/analyze", "/generate-resume", "/health"]}), 200

# ---------- ORIGINAL ENDPOINTS ----------
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
        template = data.get('template', 'modern')   # 'modern', 'professional', 'executive'
        
        # Common fields
        name = data.get('name', 'Your Name')
        role = data.get('targetRole', 'Software Developer')
        skills = data.get('skills', 'Python, JavaScript, React')
        experience = data.get('experience', '1-3 years')
        email = data.get('email', '')
        phone = data.get('phone', '')
        degree = data.get('degree', '')
        
        # Template-specific fields
        if template == 'modern':
            linkedin = data.get('linkedin', '')
            portfolio = data.get('portfolio', '')
            company = data.get('company', '')
            certs = data.get('certs', '')
            projects = data.get('projects', '')
            languages = data.get('languages', '')
            achievements = data.get('achievements', '')
            extraSkills = data.get('extraSkills', '')
            location = data.get('location', '')
            if extraSkills:
                skills = skills + ', ' + extraSkills if skills else extraSkills
            
            prompt = f"""You are an expert resume writer. Generate ONLY the text content for a resume with the following details. Do NOT include any formatting like markdown or HTML. Use plain text.

Template: Two‑column modern resume (photo on left, contact, languages, achievements, certifications on left; summary, skills, work experience, education, projects on right).

Personal:
Name: {name}
Role: {role}
Email: {email}
Phone: {phone}
Location: {location or 'City, State'}
LinkedIn: {linkedin if linkedin else 'linkedin.com/in/yourprofile'}
Portfolio: {portfolio if portfolio else 'yourportfolio.com'}

Skills: {skills}
Experience: {experience} years
Current Company: {company if company else 'Not specified'}
Education: {degree if degree else 'Bachelor of Technology in Computer Science, XYZ University, 2022'}
Certifications: {certs if certs else 'None'}
Projects: {projects if projects else 'None'}
Languages: {languages if languages else 'English, Hindi'}
Achievements: {achievements if achievements else 'None'}

Generate the following sections as plain text:
1. Professional Summary (2-3 lines, start with "Results-driven {role} with {experience} of experience...", include a metric)
2. Skills (just the list, each skill on new line starting with '-')
3. Work Experience (one entry for {role} at {company if company else 'Tech Solutions'}, with 2‑3 bullet points using quantified achievements. Use realistic metrics like percentages, numbers.)
4. Education (one line)
5. Projects (list each project on new line starting with '-')
6. Languages (comma separated, if provided)
Return only the plain text without any section headings. I will arrange them in the template."""
        
        elif template == 'professional':
            company = data.get('company', '')
            prompt = f"""Generate a professional, ATS-friendly resume in plain text for:
Name: {name}
Role: {role}
Email: {email}
Phone: {phone}
Skills: {skills}
Experience: {experience} years
Company: {company if company else 'Previous Company'}
Education: {degree if degree else 'Bachelor of Technology, XYZ University'}

Include sections: Professional Summary (2 lines, traditional), Skills (bullet points), Work Experience (one entry with 2 bullet points), Education. Use metrics where possible. Return plain text with section headings (e.g., 'Professional Summary', 'Skills', etc.)."""

        else:  # executive
            linkedin = data.get('linkedin', '')
            portfolio = data.get('portfolio', '')
            company = data.get('company', '')
            achievements = data.get('achievements', '')
            leadership = data.get('execLeadership', '')
            certs = data.get('certs', '')
            languages = data.get('languages', '')
            projects = data.get('projects', '')
            prompt = f"""Generate an executive‑level resume (FAANG style) for:
Name: {name}
Role: {role}
Email: {email}
Phone: {phone}
LinkedIn: {linkedin}
Portfolio: {portfolio}
Skills: {skills}
Experience: {experience} years
Current Company & Title: {company}
Key Achievements (comma separated, use numbers): {achievements}
Leadership Metrics: {leadership}
Certifications: {certs}
Languages: {languages}
Projects: {projects}
Education: {degree if degree else 'Executive MBA / Advanced Degree'}

Requirements:
- Use quantified metrics (%, $, number of people, time saved)
- Include a metrics highlight section (e.g., "15+ team size", "40% revenue growth")
- Professional Summary must be strategic and results‑oriented
- Skills as bullet points
- Work Experience with 2‑3 bullet points, each starting with a strong action verb and a metric
- Education, Certifications, Projects, Languages
Return plain text with clear section headings (e.g., 'Executive Summary', 'Core Competencies', 'Professional Experience', 'Education', etc.)"""

        headers = {
            'Authorization': f'Bearer {MISTRAL_API_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'mistral-small-latest',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.4,
            'max_tokens': 2500
        }
        
        print(f"Calling Mistral API for resume generation (template: {template})...")
        resp = requests.post(MISTRAL_URL, headers=headers, json=payload, timeout=60)
        print(f"Mistral response status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"Mistral error: {resp.text}")
            fallback = f"{name}\n{role}\n\nContact: {email} | {phone}\n\nProfessional Summary: Results-driven {role} with {experience} of experience.\n\nSkills:\n{skills.replace(',', '\n- ')}\n\nWork Experience:\n• {role} at {company if company else 'Tech Company'} | {experience}\n  - Improved efficiency by 25%.\n\nEducation:\n{degree}\n"
            return jsonify({"resume": fallback}), 200
            
        result = resp.json()
        resume_text = result['choices'][0]['message']['content']
        
        academic_keywords = ['covid-19', 'pandemic', 'systematic review', 'digital health', 'abstract', 'introduction', 'methodology', 'conclusion']
        if any(kw in resume_text.lower() for kw in academic_keywords):
            print("Detected academic content, using fallback.")
            fallback = f"{name}\n{role}\n\nContact: {email} | {phone}\n\nProfessional Summary: Experienced {role} with {experience} of experience.\n\nSkills:\n{skills.replace(',', '\n- ')}\n\nWork Experience:\n• {role} at {company if company else 'Tech Company'} | {experience}\n  - Achieved 30% performance improvement.\n\nEducation:\n{degree}\n"
            return jsonify({"resume": fallback}), 200
        
        return jsonify({"resume": resume_text})
        
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
