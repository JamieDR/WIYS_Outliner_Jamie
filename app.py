from flask import Flask, request, render_template, jsonify, send_file
from newspaper import Article
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
        if not para:
            continue
            
        if len(para.split()) <= 5 and len(para) < 50:
            if current_section:
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
                current_points.append(point)
    
    if current_section:
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
    urls = request.json.get('urls', [])
    results = []
    
    for url in urls:
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            outline = create_outline(article.text)
            results.append({
                'url': url,
                'title': article.title,
                'outline': outline
            })
        except Exception as e:
            results.append({
                'url': url,
                'error': str(e)
            })
    
    return jsonify(results)

@app.route('/download-outline', methods=['POST'])
def download_outline():
    data = request.json
    title = secure_filename(data['title'])
    content = data['content']
    
    filename = f"{title}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    try:
        return send_file(filename, as_attachment=True)
    finally:
        os.remove(filename)

if __name__ == '__main__':
    app.run(debug=True)
