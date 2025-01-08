# app.py
from flask import Flask, request, render_template, jsonify, send_file
import spacy
import re
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create uploads folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Load spacy model at startup
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def create_outline(text):
    # Clean the text
    text = re.sub(r'Advertisement|Sponsored Content|Share this article|Follow us|Subscribe|Sign up', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(Follow|Like|Share|Tweet|Pin).+(Facebook|Twitter|Instagram|LinkedIn|Pinterest)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Sign up for our newsletter|Get our daily newsletter|Enter your email', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Menu|Navigation|Home|About|Contact|Search', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Copyright|All rights reserved|Terms of (Use|Service)|Privacy Policy', '', text, flags=re.IGNORECASE)
    
    paragraphs = text.split('\n')
    outline = []
    
    current_section = None
    current_points = []
    
    for para in paragraphs:
        para = para.strip()
        if not para or len(para) < 10:
            continue
            
        if len(para.split()) <= 5 and len(para) < 50:
            if current_section and current_points:
                outline.append({
                    "header": current_section,
                    "points": current_points
                })
            current_section = para
            current_points = []
        else:
            doc = nlp(para)
            for sent in doc.sents:
                point = sent.text.strip()
                point = re.sub(r'^(There are|There is|It is|This is)\s+', '', point)
                point = point.rstrip('.')
                
                if len(point.split()) > 3:
                    current_points.append(point)
    
    if current_section and current_points:
        outline.append({
            "header": current_section,
            "points": current_points
        })
    
    # Remove any empty sections
    outline = [section for section in outline if section['points']]
    return outline

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate-outlines', methods=['POST'])
def generate_outlines():
    results = []
    
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
        
    files = request.files.getlist('files[]')
    
    for file in files:
        if file.filename == '':
            continue
            
        try:
            # Read and decode the file content
            content = file.read().decode('utf-8')
            
            # Create outline from file content
            outline = create_outline(content)
            
            if outline:
                # Use filename without extension as title
                title = os.path.splitext(file.filename)[0]
                results.append({
                    'filename': file.filename,
                    'title': title,
                    'outline': outline
                })
            else:
                results.append({
                    'filename': file.filename,
                    'error': 'Could not extract meaningful content from this file'
                })
                
        except Exception as e:
            results.append({
                'filename': file.filename,
                'error': str(e)
            })
    
    return jsonify(results)

@app.route('/download-outline', methods=['POST'])
def download_outline():
    data = request.json
    title = secure_filename(data['title'])
    content = data['content']
    
    filename = f"{title}_outline.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    try:
        return send_file(filename, as_attachment=True)
    finally:
        os.remove(filename)

if __name__ == '__main__':
    app.run(debug=True)
