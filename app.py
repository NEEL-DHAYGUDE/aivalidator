from flask import Flask, request, render_template_string, session, redirect
import fitz  # PyMuPDF
from mistralai import Mistral
import requests
import uuid

app = Flask(__name__)
# In a real production app, change this to a random string of characters
app.secret_key = "super_secure_secret_key_change_this"

# ==========================================
# CONFIGURATION
# ==========================================
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLrFTMKtPGozjmKez8Za2ubTGdKVJnO_G5OlvOMltHdR2kIGvkRZ9rxYKzPJzhr1J7/exec"

# ==========================================
# HTML TEMPLATES (Premium Tech UI)
# ==========================================
HTML_BASE = """
<!DOCTYPE html>
<html>
<head>
    <title>Nazar.ai | Enterprise Validation Engine</title>
    <style>
        /* Tech Themed Background */
        body { 
            background-color: #0B0F19; 
            background-image: 
                radial-gradient(circle at 50% 0%, #1e293b 0%, transparent 70%),
                linear-gradient(rgba(14, 165, 233, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(14, 165, 233, 0.03) 1px, transparent 1px);
            background-size: 100% 100%, 30px 30px, 30px 30px;
            color: #F8FAFC; 
            font-family: 'Segoe UI', sans-serif; 
            margin: 0; 
            display: flex; 
            flex-direction: column; 
            min-height: 100vh; 
        }
        
        /* Premium Header */
        .navbar { display: flex; justify-content: space-between; align-items: center; padding: 20px 50px; background-color: rgba(17, 24, 39, 0.9); border-bottom: 1px solid #1E293B; backdrop-filter: blur(10px); }
        .navbar-brand a { font-size: 26px; font-weight: bold; color: #0EA5E9; letter-spacing: 2px; text-transform: uppercase; text-decoration: none; }
        .navbar-links { font-size: 14px; }
        .navbar-links a { color: #F8FAFC; text-decoration: none; font-weight: bold; transition: 0.2s; margin-left: 30px; letter-spacing: 1px; }
        .navbar-links a:hover { color: #0EA5E9; }
        
        /* Main Layout */
        .main-content { flex: 1; padding: 50px 20px; display: flex; flex-direction: column; justify-content: center; align-items: center;}
        .container { width: 100%; max-width: 950px; background-color: #111827; padding: 40px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.6); border: 1px solid #1E293B; }
        
        h1 { color: #0EA5E9; }
        h3 { color: #94A3B8; }
        input, button { padding: 14px; margin-top: 10px; margin-bottom: 20px; width: 100%; border-radius: 6px; border: none; box-sizing: border-box; font-size: 11pt; }
        input { background-color: #1E293B; color: white; border: 1px solid #334155; transition: 0.3s; }
        input:focus { outline: none; border-color: #0EA5E9; }
        input[type="file"] { padding: 12px; background-color: #0f172a; border: 1px dashed #334155; color: #94A3B8; cursor: pointer; }
        
        button { background-color: #0EA5E9; color: white; font-weight: bold; cursor: pointer; text-transform: uppercase; letter-spacing: 1.5px; transition: 0.3s; }
        button:hover { background-color: #38BDF8; box-shadow: 0 0 20px rgba(14, 165, 233, 0.4); }
        
        .public-notice { background-color: #1E293B; padding: 25px; border-left: 4px solid #0EA5E9; margin-bottom: 20px; border-radius: 6px; }
        .report-box { background-color: #ffffff; color: #333333; padding: 40px; margin-top: 30px; border-radius: 8px; font-family: Arial, sans-serif; overflow-x: auto; }
        .report-box table { width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px;}
        .report-box th, .report-box td { border: 1px solid #d1d5db; padding: 10px; text-align: left; }
        .report-box th { background-color: #1E293B; color: #F8FAFC; }
        .api-note { font-size: 0.85em; color: #64748B; margin-top: -15px; margin-bottom: 20px; display: block; }
        
        /* Premium Footer */
        .footer { text-align: center; padding: 25px; background-color: #0f172a; color: #64748b; border-top: 1px solid #1E293B; font-size: 13px; margin-top: auto; line-height: 1.8; }
        .footer span { color: #94A3B8; font-weight: bold; }
        
        /* Interactive Loading Spinner CSS */
        .loader-container { display: none; text-align: center; padding: 60px 0; }
        .spinner { width: 70px; height: 70px; border: 6px solid rgba(14, 165, 233, 0.1); border-left-color: #0EA5E9; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 25px auto; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .blinking-text { animation: blinker 1.5s linear infinite; color: #0EA5E9; font-weight: bold; letter-spacing: 2px; margin-bottom: 10px; }
        @keyframes blinker { 50% { opacity: 0.4; } }
        /* This hides the website UI when printing to PDF (Ctrl+P) */
        /* This hides the website UI when printing to PDF (Ctrl+P) */
        @media print {
            .navbar, .footer, button, .api-note, hr, .navbar-links, .navbar-brand {
                display: none !important;
            }
            body { background: white !important; }
            .container { 
                background: white !important; 
                color: black !important; 
                box-shadow: none !important; 
                border: none !important;
                max-width: 100% !important;
                padding: 0 !important;
                margin: 0 !important;
            }
            .report-box { padding: 0 !important; margin: 0 !important; border: none !important; }
            h1, h2, h3, p, b, li { color: black !important; }
        }
    </style>
    
    <script>
        function showLoader(loadingText) {
            document.getElementById('form-container').style.display = 'none';
            document.getElementById('loader-container').style.display = 'block';
            if (loadingText) {
                document.getElementById('loader-text').innerText = loadingText;
            }
        }
    </script>
</head>
<body>
    <div class="navbar">
        <div class="navbar-brand"><a href="/">NAZAR.AI</a></div>
        <div class="navbar-links">
            <a href="/login">LOGIN</a>
            <a href="/contact">CONTACT US</a>
        </div>
    </div>

    <div class="main-content">
        <div id="loader-container" class="loader-container" style="width: 100%;">
            <div class="spinner"></div>
            <h2 class="blinking-text" id="loader-text">PROCESSING...</h2>
            <p style="color: #94A3B8;">Please wait. Deep document analysis can take up to 60 seconds.</p>
        </div>
        
        <div id="form-container" style="width: 100%; display: flex; justify-content: center;">
            {{ content|safe }}
        </div>
    </div>

    <div class="footer">
        &copy; 2026 Nazar.ai. All Rights Reserved.<br>
        Developed by <span>Neel Dhaygude</span> | Contact: <span>+91 7984783550</span>
    </div>
</body>
</html>
"""

# ==========================================
# WEB ROUTES
# ==========================================

@app.route("/")
def public_home():
    """Page 1: The Public Facing Landing Page (No Login Form)"""
    content = """
        <div class="container" style="background-color: rgba(17, 24, 39, 0.8);">
            <div style="text-align: center; margin-bottom: 45px;">
                <h1 style="font-size: 38px; margin-bottom: 10px; color: #F8FAFC;">Enterprise Validation Engine</h1>
                <p style="color: #0EA5E9; font-size: 18px; font-weight: bold; letter-spacing: 1px;">Powered by Advanced Mistral RAG Architecture</p>
            </div>
            
            <div class="public-notice">
                <h3 style="color: #F8FAFC; margin-top: 0; border-bottom: 1px solid #334155; padding-bottom: 10px;">⚡ System Capabilities</h3>
                <ul style="color: #94A3B8; line-height: 1.8; padding-left: 20px; font-size: 16px;">
                    <li><b>Precision Matching:</b> Cross-reference massive vendor proposals against corporate master specs instantly.</li>
                    <li><b>Deviation Tracking:</b> Automatically flag missing clauses, material mismatches, and compliance risks.</li>
                    <li><b>Quantitative Scoring:</b> Generate rigid, objective Safety & Compliance scores out of 100.</li>
                    <li><b>Enterprise Security:</b> Zero-retention document ingestion with strict hardware-locked access.</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin-top: 40px;">
                <a href="/login"><button style="width: auto; padding: 15px 40px; font-size: 16px;">ACCESS CLIENT PORTAL</button></a>
            </div>
        </div>
    """
    return render_template_string(HTML_BASE, content=content)


@app.route("/login", methods=["GET", "POST"])
def login_page():
    """Page 2: The Dedicated Login Page"""
    if request.method == "POST":
        license_key = request.form.get("license_key").strip()
        
        if "device_id" not in session:
            session["device_id"] = str(uuid.uuid4())
            
        payload = {"license_key": license_key, "device_id": session["device_id"]}
        
        try:
            response = requests.get(GOOGLE_SCRIPT_URL, params=payload, timeout=15)
            result = response.json()
            
            if result.get("status") == "success":
                session["logged_in"] = True
                session["client_name"] = license_key
                return redirect("/dashboard")
            else:
                error_msg = result.get("message", "Invalid License")
                return render_template_string(HTML_BASE, content=f"<div class='container' style='max-width: 500px; text-align: center;'><h1>Access Denied</h1><p style='color: #ef4444; font-weight: bold;'>{error_msg}</p><a href='/login'><button>Try Again</button></a></div>")
                
        except Exception as e:
            return render_template_string(HTML_BASE, content=f"<div class='container' style='max-width: 500px; text-align: center;'><h1>Network Error</h1><p>Could not connect to license server: {str(e)}</p><a href='/login'><button>Try Again</button></a></div>")

    content = """
        <div class="container" style="max-width: 450px;">
            <h2 style="color: #F8FAFC; margin-top: 0; text-align: center; margin-bottom: 5px;">Client Login</h2>
            <p style="text-align: center; color: #64748B; font-size: 13px; margin-bottom: 30px;">Enter your hardware-locked license key to securely access the analysis dashboard.</p>
            
            <form method="POST" onsubmit="showLoader('VERIFYING LICENSE...')">
                <label style="color: #94A3B8; font-size: 12px; font-weight: bold; text-transform: uppercase;">License Key</label>
                <input type="text" name="license_key" placeholder="e.g., XYZ-123" required>
                <button type="submit" style="margin-top: 15px;">AUTHENTICATE</button>
            </form>
        </div>
    """
    return render_template_string(HTML_BASE, content=content)


@app.route("/contact")
def contact_page():
    """Page 3: Contact Details"""
    content = """
        <div class="container" style="max-width: 550px; text-align: center;">
            <h1 style="color: #0EA5E9; margin-bottom: 30px;">Contact Nazar.ai</h1>
            
            <div style="background-color: #1E293B; padding: 40px; border-radius: 8px; border-left: 4px solid #0EA5E9; text-align: left;">
                <p style="font-size: 18px; color: #F8FAFC; margin-bottom: 20px;">
                    <b style="color: #94A3B8; margin-right: 10px;">Name:</b> Neel Dhaygude
                </p>
                <p style="font-size: 18px; color: #F8FAFC; margin-bottom: 20px;">
                    <b style="color: #94A3B8; margin-right: 10px;">Phone:</b> +91 7984783550
                </p>
                <p style="font-size: 18px; color: #F8FAFC;">
                    <b style="color: #94A3B8; margin-right: 10px;">Email:</b> <a href="mailto:neeldhaygude7@gmail.com" style="color: #0EA5E9; text-decoration: none;">neeldhaygude7@gmail.com</a>
                </p>
            </div>
        </div>
    """
    return render_template_string(HTML_BASE, content=content)


@app.route("/dashboard", methods=["GET", "POST"])
def secure_dashboard():
    """The Private App (Only accessible if paid/logged in via Google Sheets)"""
    if not session.get("logged_in"):
        return redirect("/login")

    if request.method == "POST":
        api_key = request.form.get("api_key")
        master_file = request.files.get("master_doc")
        target_file = request.files.get("target_doc")
        
        if api_key and master_file and target_file:
            try:
                master_text = extract_text_from_stream(master_file.read())[:30000]
                target_text = extract_text_from_stream(target_file.read())[:30000]
                
                report_html = run_ai_audit(api_key, master_text, target_text)
                
                result_content = f"""
                    <div class="container">
                        <h1>Audit Complete for License: {session['client_name']}</h1>
                        <p style="color: #10B981; font-weight: bold;">✓ Analysis successful. Press <b>Ctrl+P</b> to save this report as a PDF.</p>
                        <div class="report-box">
                            {report_html}
                        </div>
                        <br>
                        <a href='/dashboard'><button style='background-color: #1E293B;'>Run Another Audit</button></a>
                    </div>
                """
                return render_template_string(HTML_BASE, content=result_content)
                
            except Exception as e:
                 error_content = f"""
                    <div class="container" style="max-width: 600px;">
                        <h1>Analysis Failed</h1>
                        <div class="public-notice" style="border-left-color: #ef4444;">
                            <p><strong>System Error:</strong> {str(e)}</p>
                            <p>Please check your Mistral API key and ensure your PDFs are not password protected.</p>
                        </div>
                        <a href='/dashboard'><button>Return to Dashboard</button></a>
                    </div>
                 """
                 return render_template_string(HTML_BASE, content=error_content)

    dashboard_content = f"""
        <div class="container">
            <h1>License Active: {session['client_name']}</h1>
            <p>Configure your engine and upload your specifications below to execute a compliance audit.</p>
            <hr style="border-color: #1E293B; margin: 30px 0;">
            
            <form method="POST" enctype="multipart/form-data" onsubmit="showLoader('EXECUTING COMPLIANCE AUDIT...')">
                <h3>1. AI Engine Configuration</h3>
                <label style="color: #F8FAFC; font-weight: bold; font-size: 14px;">Mistral API Key</label>
                <input type="password" name="api_key" placeholder="Enter your Mistral API Key (e.g., aBcD123...)" required>
                <span class="api-note">Your key is used strictly for this transaction and is not stored on our servers.</span>
                
                <h3 style="margin-top: 30px;">2. Document Ingestion</h3>
                <label style="color: #F8FAFC; font-weight: bold; font-size: 14px;">Master Specification (Rules)</label>
                <input type="file" name="master_doc" accept=".pdf" required>
                
                <label style="color: #F8FAFC; font-weight: bold; font-size: 14px; margin-top: 15px; display: block;">Vendor Proposal (Target)</label>
                <input type="file" name="target_doc" accept=".pdf" required>
                
                <button type="submit" style="margin-top: 40px; padding: 18px; font-size: 16px;">EXECUTE AI COMPLIANCE AUDIT</button>
            </form>
            <br>
            <div style="text-align: center;">
                <a href='/logout' style='color: #ef4444; text-decoration: none; font-weight: bold; font-size: 14px;'>[ Secure Logout ]</a>
            </div>
        </div>
    """
    return render_template_string(HTML_BASE, content=dashboard_content)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ==========================================
# CORE LOGIC 
# ==========================================

def extract_text_from_stream(pdf_bytes):
    """Reads the raw bytes of the uploaded PDF file without saving it to the server's hard drive."""
    text = ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text += page.get_text() + "\n"
        return text
    except Exception as e:
        raise Exception(f"PDF Parsing Error: {str(e)}")

def run_ai_audit(api_key, master_text, target_text):
    """Sends the data to Mistral and forces HTML output."""
    prompt = f"""
    You are an elite B2B Engineering & Compliance Auditor. 
    
    DOCUMENT 1: COMPANY MASTER SPECIFICATIONS (The rules): 
    {master_text}
    
    DOCUMENT 2: VENDOR PROPOSAL (The document to audit): 
    {target_text}
    
    TASK: 
    1. Compare Document 2 against Document 1. 
    2. Give a precise "Safety & Compliance Score" out of 100.
    3. Explain EXACTLY why this score was given.
    4. List all critical deviations, missing clauses, or hazardous materials.
    
    FORMATTING RULES (CRITICAL):
    - Output the ENTIRE report using ONLY basic HTML tags (<h2>, <h3>, <p>, <b>, <ul>, <li>).
    - For tables, you MUST strictly use this exact HTML structure with these attributes:
      <table border="1" width="100%">
        <thead><tr><th bgcolor="#1E293B"><font color="#ffffff">Header 1</font></th></tr></thead>
        <tbody><tr><td>Data 1</td></tr></tbody>
      </table>
    - Do NOT use ANY Markdown formatting (no asterisks **, no hashes ##, no pipes |).
    - Do NOT wrap your response in ```html code blocks. Output raw HTML text only.
    - Be highly professional, rigid, and analytical.
    """
    
    client = Mistral(api_key=api_key.strip())
    response = client.chat.complete(
        model="mistral-large-latest", 
        messages=[
            {"role": "system", "content": "You are an automated corporate audit system. Output strict, clean HTML only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    # This strips away the ```html and ``` tags if the AI includes them
    # This strips away any markdown code blocks returned by the AI
    raw_content = response.choices[0].message.content
    clean_content = raw_content.replace("```html", "").replace("```HTML", "").replace("```", "").strip()
    return clean_content
if __name__ == "__main__":
    import os
    # Render provides a PORT environment variable. We MUST use it.
    port = int(os.environ.get("PORT", 8080))
    # host='0.0.0.0' tells the app to listen to all public requests
    app.run(host='0.0.0.0', port=port)


