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
        name = data.get('name', 'Your Name')
        role = data.get('targetRole', 'Software Developer')
        skills = data.get('skills', 'Python, JavaScript, React')
        exp = data.get('experience', '1-3 years')
        
        # Additional fields (optional) – frontend se bheje to le lo
        email = data.get('email', '')
        phone = data.get('phone', '')
        linkedin = data.get('linkedin', '')
        portfolio = data.get('portfolio', '')
        company = data.get('company', '')
        degree = data.get('degree', '')
        certs = data.get('certs', '')
        projects = data.get('projects', '')
        languages = data.get('languages', '')
        template = data.get('template', 'modern')

        # Build a powerful, strict prompt
        prompt = f"""You are an expert professional resume writer. Your task: generate a REAL, ready-to-use resume for a human job seeker. 
DO NOT write research papers, abstracts, literature reviews, COVID-19 related content, or any academic text. 
DO NOT include placeholders like "[...]". Use realistic examples.

The resume must follow this exact structure with QUANTIFIED ACHIEVEMENTS (use numbers, percentages, metrics):

{name}
{role}

Contact: {email if email else 'your.email@example.com'} | {phone if phone else '+91 9876543210'} | LinkedIn: {linkedin if linkedin else 'linkedin.com/in/yourprofile'} | Portfolio: {portfolio if portfolio else 'yourportfolio.com'}

Professional Summary:
(2-3 lines. Start with "Results-driven {role} with {exp} of experience...". Include a metric like "improved X by Y%")

Skills:
- {skills.replace(',', '\n- ')}

Work Experience:
• {role} at {company if company else 'TechCorp Solutions'} | {exp}
  - [Achievement with metric, e.g., "Led migration to cloud, reducing costs by 30%"]
  - [Another achievement with metric, e.g., "Automated testing, cutting deployment time by 50%"]
  - [Third achievement]

• (Previous role) Junior {role} at Previous Company | (2 years before)
  - [Achievement with metric]
  - [Achievement with metric]

Education:
{degree if degree else 'Bachelor of Technology in Computer Science, XYZ University, 2022'}

Certifications:
{certs if certs else 'AWS Certified Cloud Practitioner, Google IT Automation'}

Projects:
{projects if projects else '• E-commerce Platform: Built full-stack app serving 500+ daily users\n• AI Chatbot: Reduced response time by 40%'}

Languages:
{languages if languages else 'English (fluent), Hindi (native)'}

Return ONLY plain text, no markdown, no extra comments. The text should be ready to copy-paste as a resume."""

        headers = {
            'Authorization': f'Bearer {MISTRAL_API_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'mistral-small-latest',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.4,  # lower temperature for more deterministic output
            'max_tokens': 2500
        }
        
        print("Calling Mistral API for resume generation...")
        resp = requests.post(MISTRAL_URL, headers=headers, json=payload, timeout=60)
        print(f"Mistral response status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"Mistral error: {resp.text}")
            # Fallback to a simple template
            fallback_resume = f"""{name}
{role}

Contact: {email if email else 'your.email@example.com'} | {phone if phone else '+91 9876543210'}

Professional Summary:
Results-driven {role} with {exp} of experience. Skilled in {skills}. Proven track record of delivering projects on time.

Skills:
{skills.replace(',', '\n- ')}

Work Experience:
• {role} at {company if company else 'Tech Company'} | {exp}
  - Improved system efficiency by 25%.
  - Implemented new features leading to 15% user growth.

Education:
{degree if degree else 'Bachelor\'s in Computer Science'}

Certifications:
{certs if certs else 'Professional Certification'}

Projects:
{projects if projects else '• Key project demonstrating technical skills'}

Languages:
{languages if languages else 'English'}

References available upon request."""
            return jsonify({"resume": fallback_resume}), 200
            
        result = resp.json()
        resume_text = result['choices'][0]['message']['content']
        
        # Optional: crude check for academic keywords – if found, use fallback
        academic_keywords = ['covid-19', 'pandemic', 'systematic review', 'digital health', 'abstract', 'introduction', 'methodology', 'conclusion']
        lower_text = resume_text.lower()
        if any(keyword in lower_text for keyword in academic_keywords):
            print("Detected academic content, using fallback.")
            # Use same fallback as above (you can reuse code)
            fallback_resume = f"""{name}
{role}

Contact: {email if email else 'your.email@example.com'} | {phone if phone else '+91 9876543210'}

Professional Summary:
Results-driven {role} with {exp} of experience. Skilled in {skills}. Proven ability to deliver high-quality solutions.

Skills:
{skills.replace(',', '\n- ')}

Work Experience:
• {role} at {company if company else 'Tech Company'} | {exp}
  - Achieved 30% performance improvement.
  - Reduced costs by 20% through optimization.

Education:
{degree if degree else 'Bachelor\'s in Computer Science'}

Certifications:
{certs if certs else 'Certified Professional'}

Projects:
{projects if projects else '• Major project with measurable impact'}

Languages:
{languages if languages else 'English'}"""
            return jsonify({"resume": fallback_resume}), 200
        
        return jsonify({"resume": resume_text})
        
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
