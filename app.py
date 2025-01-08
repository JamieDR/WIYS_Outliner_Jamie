# app.py
from flask import Flask, request, render_template, jsonify, send_file
import spacy
import re
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Load spacy model at startup
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def create_outline(text):
    paragraphs = text.split('\n')
    outline = []
    
    current_section = None
    current_points = []
    
    for para in paragraphs:
        para = para.strip()
        if not para or len(para) < 10:
            continue
            
        # Check if this is likely a header
        if len(para.split()) <= 5 and len(para) < 50:
            # Save previous section if it exists
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
                point = point.rstrip('.')
                if len(point.split()) > 3:
                    current_points.append(point)
    
    # Add the last section
    if current_section and current_points:
        outline.append({
            "header": current_section,
            "points": current_points
        })
    
    return outline

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate-outlines', methods=['POST'])
def generate_outlines():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
        
    files = request.files.getlist('files[]')
    results = []
    
    for file in files:
        if file.filename == '' or not file.filename.endswith('.txt'):
            continue
            
        try:
            content = file.read().decode('utf-8')
            outline = create_outline(content)
            
            if outline:
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
