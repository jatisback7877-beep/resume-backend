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

# -------------------------------------------------------------------
# HTML/CSS template – exactly like the provided PDF resume
# (two‑column layout, similar colors, fonts, spacing, image placeholder)
# -------------------------------------------------------------------
RESUME_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - Resume</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: #eef2f5;
            font-family: 'Segoe UI', 'Poppins', Roboto, 'Helvetica Neue', sans-serif;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .resume-card {{
            max-width: 1000px;
            width: 100%;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 35px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: all 0.2s;
        }}
        /* two‑column layout */
        .resume-inner {{
            display: flex;
            flex-wrap: wrap;
        }}
        /* left sidebar – dark blueish background */
        .sidebar {{
            flex: 1.2;
            background: #1e2a5e;
            color: #f0f3fa;
            padding: 30px 20px;
        }}
        /* right main content – clean white */
        .main-content {{
            flex: 2.2;
            background: white;
            padding: 30px 30px 30px 25px;
        }}
        /* photo placeholder (circle) */
        .photo {{
            text-align: center;
            margin-bottom: 25px;
        }}
        .photo img {{
            width: 140px;
            height: 140px;
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid #ffb347;
            background: #fff;
        }}
        .photo .no-img {{
            width: 140px;
            height: 140px;
            border-radius: 50%;
            background: #2d3a6e;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
            font-size: 50px;
            color: #ffb347;
            border: 2px solid #ffb347;
        }}
        /* sidebar headings */
        .sidebar h3 {{
            font-size: 1.2rem;
            letter-spacing: 1px;
            border-left: 4px solid #ffb347;
            padding-left: 12px;
            margin: 25px 0 15px 0;
            color: #ffd966;
        }}
        .sidebar .contact-info p {{
            margin: 8px 0;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .sidebar .section {{
            margin-bottom: 25px;
        }}
        .sidebar ul {{
            list-style: none;
            padding-left: 5px;
        }}
        .sidebar li {{
            margin-bottom: 8px;
            font-size: 0.9rem;
            position: relative;
            padding-left: 18px;
        }}
        .sidebar li::before {{
            content: "▹";
            position: absolute;
            left: 0;
            color: #ffb347;
        }}
        /* right side headings */
        .main-content h2 {{
            font-size: 1.6rem;
            color: #1e2a5e;
            border-bottom: 3px solid #ffb347;
            padding-bottom: 6px;
            margin: 20px 0 15px 0;
            display: inline-block;
        }}
        .main-content h1 {{
            font-size: 2.5rem;
            color: #1e2a5e;
            margin: 0 0 5px 0;
        }}
        .main-content .role-tag {{
            font-size: 1.1rem;
            color: #ff8c42;
            font-weight: 500;
            margin-bottom: 15px;
        }}
        .summary {{
            background: #f9fafc;
            padding: 12px 18px;
            border-radius: 14px;
            margin: 10px 0 20px;
            line-height: 1.5;
            color: #2c3e66;
        }}
        .skills-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 12px 0 15px;
        }}
        .skill-badge {{
            background: #eef2ff;
            color: #1e2a5e;
            padding: 5px 14px;
            border-radius: 30px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        .experience-item, .edu-item {{
            margin-bottom: 18px;
        }}
        .exp-title {{
            font-weight: 700;
            font-size: 1rem;
            color: #1e2a5e;
        }}
        .exp-date {{
            font-size: 0.8rem;
            color: #ff8c42;
            margin-bottom: 6px;
        }}
        ul.achievement-list {{
            padding-left: 20px;
            margin: 5px 0;
        }}
        ul.achievement-list li {{
            margin-bottom: 5px;
            font-size: 0.85rem;
        }}
        hr {{
            margin: 8px 0;
            border: 0;
            height: 1px;
            background: #ddd;
        }}
        @media (max-width: 700px) {{
            .resume-inner {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
<div class="resume-card">
    <div class="resume-inner">
        <!-- LEFT SIDEBAR (photo, contact, languages, achievements) -->
        <div class="sidebar">
            <div class="photo">
                {photo_html}
            </div>
            <div class="section">
                <h3>📞 CONTACT</h3>
                <div class="contact-info">
                    <p>📧 {email}</p>
                    <p>📞 {phone}</p>
                    <p>📍 {location}</p>
                    {linkedin_html}
                    {portfolio_html}
                </div>
            </div>
            <div class="section">
                <h3>🗣️ LANGUAGES</h3>
                <ul>
                    {languages_html}
                </ul>
            </div>
            <div class="section">
                <h3>🏆 ACHIEVEMENTS</h3>
                <ul>
                    {achievements_html}
                </ul>
            </div>
            {certs_sidebar_html}
        </div>

        <!-- RIGHT MAIN CONTENT -->
        <div class="main-content">
            <h1>{name}</h1>
            <div class="role-tag">{target_role}</div>
            
            <div class="summary">
                {summary}
            </div>

            <h2>🛠️ SKILLS</h2>
            <div class="skills-list">
                {skills_html}
            </div>

            <h2>💼 WORK EXPERIENCE</h2>
            {experience_html}

            <h2>🎓 EDUCATION</h2>
            {education_html}

            {projects_html_extra}
        </div>
    </div>
</div>
</body>
</html>
"""

def build_resume_html(data):
    """
    data: dict with fields from frontend (name, email, phone, targetRole, skills, experience, etc.)
    Returns complete HTML string matching the given resume style.
    """
    name = data.get('name', 'Hitesh jaat')
    target_role = data.get('targetRole', 'BCA Student & Digital Marketing Enthusiast')
    email = data.get('email', 'jatisback7877@gmail.com')
    phone = data.get('phone', '7877366068')
    location = data.get('location', 'bhadsoa, chittorgarh, India 312024')
    linkedin = data.get('linkedin', '')
    portfolio = data.get('portfolio', '')
    
    # languages: list or string
    languages = data.get('languages', 'Hindi (First Language), English (B1 Intermediate)')
    if isinstance(languages, str):
        languages = [lang.strip() for lang in languages.split(',')]
    languages_html = ''.join([f'<li>{lang}</li>' for lang in languages])
    
    # achievements
    achievements = data.get('achievements', [
        "Active participant in college technical activities",
        "Completed multiple online learning modules in digital marketing and programming"
    ])
    if isinstance(achievements, str):
        achievements = [a.strip() for a in achievements.split('\n') if a.strip()]
    achievements_html = ''.join([f'<li>{ach}</li>' for ach in achievements])
    
    # summary
    summary = data.get('summary', "Motivated BCA 5th Semester student with strong interest in Digital Marketing and Software Development. Skilled in Adobe Photoshop, Premiere Pro, C++ and Java programming. Passionate about creating impactful digital content and continuously improving technical skills to contribute effectively to organizational growth.")
    
    # skills
    skills = data.get('skills', "Digital Marketing (SEO & Social Media), C++ & Java Programming, Basic Analytics, Adobe Photoshop, Adobe Premiere Pro")
    if isinstance(skills, str):
        skills_list = [s.strip() for s in skills.split(',')]
    else:
        skills_list = skills
    skills_html = ''.join([f'<div class="skill-badge">{skill}</div>' for skill in skills_list])
    
    # work experience (from frontend or default)
    experience = data.get('experience', '')
    if not experience:
        # default from PDF style
        experience = """<div class="experience-item">
            <div class="exp-title">Technical Intern / Freelance</div>
            <div class="exp-date">2024 – Present</div>
            <ul class="achievement-list">
                <li>Assisted in digital marketing campaigns, increasing reach by 25%</li>
                <li>Developed small-scale C++ applications for local businesses</li>
            </ul>
        </div>"""
    else:
        # if user provided plain text, wrap minimally
        experience = f'<div class="experience-item">{experience}</div>'
    
    # education
    degree = data.get('degree', 'Bachelor of Computer Applications (BCA)')
    college = data.get('college', 'U.S. Ostwal P.G. College, Mangalwad, Rajasthan')
    grad_year = data.get('grad_year', '2026')
    edu_details = data.get('edu_details', 'C++ Programming, Java Programming, Python, HTML/CSS, Digital Marketing, SEO, Google Ads, Video Editing')
    education_html = f"""
    <div class="edu-item">
        <div class="exp-title">{degree} | Computer Applications</div>
        <div class="exp-date">{college} • {grad_year}</div>
        <ul class="achievement-list">
            <li>{edu_details.replace(',', '</li><li>')}</li>
        </ul>
    </div>
    """
    
    # certifications (optional)
    certs = data.get('certs', '')
    certs_sidebar_html = ''
    if certs:
        cert_list = certs.split(',') if isinstance(certs, str) else certs
        cert_items = ''.join([f'<li>{c.strip()}</li>' for c in cert_list])
        certs_sidebar_html = f'<div class="section"><h3>📜 CERTIFICATIONS</h3><ul>{cert_items}</ul></div>'
    
    # projects (optional)
    projects = data.get('projects', '')
    projects_html_extra = ''
    if projects:
        proj_items = projects.split('\n') if isinstance(projects, str) else projects
        proj_bullets = ''.join([f'<li>{p.strip()}</li>' for p in proj_items if p.strip()])
        projects_html_extra = f'<h2>📁 PROJECTS</h2><ul class="achievement-list">{proj_bullets}</ul>'
    
    # photo handling: use provided URL or default avatar
    photo_url = data.get('photo_url', '')
    if photo_url:
        photo_html = f'<img src="{photo_url}" alt="profile">'
    else:
        # default silhouette icon as placeholder
        photo_html = '<div class="no-img">📷</div>'
    
    linkedin_html = f'<p>🔗 {linkedin}</p>' if linkedin else ''
    portfolio_html = f'<p>🌐 {portfolio}</p>' if portfolio else ''
    
    return RESUME_HTML_TEMPLATE.format(
        name=name,
        target_role=target_role,
        email=email,
        phone=phone,
        location=location,
        linkedin_html=linkedin_html,
        portfolio_html=portfolio_html,
        languages_html=languages_html,
        achievements_html=achievements_html,
        summary=summary,
        skills_html=skills_html,
        experience_html=experience,
        education_html=education_html,
        certs_sidebar_html=certs_sidebar_html,
        projects_html_extra=projects_html_extra,
        photo_html=photo_html
    )

# -------------------------------------------------------------------
# MODIFIED /generate-resume endpoint – returns HTML that looks exactly
# like the provided PDF resume (format, colors, layout)
# -------------------------------------------------------------------
@app.route('/generate-resume', methods=['POST'])
def generate_resume():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Merge any AI‑enhanced content (optional, you can still call Mistral)
        # For simplicity, we use provided fields + fallback values that match the PDF style.
        # If you want AI to polish summary/achievements, uncomment the Mistral call.
        
        # Build the HTML using the exact same layout & colors as the sample PDF
        html_resume = build_resume_html(data)
        
        # Return as JSON with the HTML string (frontend can inject into iframe or div)
        return jsonify({"resume": html_resume, "format": "html"})
    
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------------------
# Keep /analyze endpoint as it was (unchanged)
# -------------------------------------------------------------------
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

        headers = {'Authorization': f'Bearer {MISTRAL_API_KEY}', 'Content-Type': 'application/json'}
        payload = {
            'model': 'mistral-small-latest',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.3,
            'max_tokens': 2000
        }
        resp = requests.post(MISTRAL_URL, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
