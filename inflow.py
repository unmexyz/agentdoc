import requests
import base64
import qrcode
from flask import Flask, render_template_string, request
from io import BytesIO
import time

# --- CONFIGURATION ---
GITHUB_USER = "yourusername"
GITHUB_REPO = "pdf-public"
GITHUB_TOKEN = "ghp_xxx..."  # Your personal access token
PDFS_FOLDER = "pdfs"
BRANCH = "main"
GITHUB_PAGES_BASE = f"https://{GITHUB_USER}.github.io/{GITHUB_REPO}/{PDFS_FOLDER}/"

app = Flask(__name__)

HTML_FORM = '''
<!doctype html>
<title>Auto-upload PDF to GitHub Pages & QR</title>
<h2>Upload PDF, auto-publish to GitHub Pages, get QR</h2>
<form method=post enctype=multipart/form-data>
  PDF: <input type=file name=pdf><br>
  <input type=submit value=Upload>
</form>
{% if qr %}
    <h3>QR Code for PDF Link:</h3>
    <img src="data:image/png;base64,{{ qr }}" alt="QR Code"><br>
    <a href="{{ link }}" target="_blank">PDF Link</a>
{% endif %}
'''

def upload_pdf_to_github(pdf_file, filename):
    # Get the SHA of the latest commit on the branch
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{PDFS_FOLDER}/{filename}"
    content = base64.b64encode(pdf_file.read()).decode()
    message = f"Add {filename}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    # Check if file exists (for update)
    get_resp = requests.get(api_url, headers=headers)
    if get_resp.status_code == 200:
        sha = get_resp.json()["sha"]
    else:
        sha = None
    data = {
        "message": message,
        "content": content,
        "branch": BRANCH
    }
    if sha:
        data["sha"] = sha
    put_resp = requests.put(api_url, headers=headers, json=data)
    if put_resp.status_code not in (200, 201):
        raise Exception(f"GitHub upload failed: {put_resp.text}")
    return f"{GITHUB_PAGES_BASE}{filename}"

@app.route('/', methods=['GET', 'POST'])
def index():
    qr_img = None
    pdf_link = None
    if request.method == 'POST':
        pdf = request.files['pdf']
        if not pdf:
            return "No PDF uploaded", 400
        filename = pdf.filename
        # Upload to GitHub
        pdf.seek(0)
        pdf_link = upload_pdf_to_github(pdf, filename)
        # Wait a few seconds for GitHub Pages to update (optional, but recommended)
        time.sleep(5)
        # Generate QR code
        qr = qrcode.make(pdf_link)
        qr_io = BytesIO()
        qr.save(qr_io, format='PNG')
        qr_io.seek(0)
        qr_img = base64.b64encode(qr_io.read()).decode()
    return render_template_string(HTML_FORM, qr=qr_img, link=pdf_link)

if __name__ == '__main__':
    app.run(port=5003, debug=True)