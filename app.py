# app.py
from flask import Flask, request, render_template, jsonify, send_file
import openai
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
openai.api_key = os.environ.get('OPENAI_API_KEY')

def create_outline(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """You will be given an article. Transform that into an outline, with each section broken down into its key facts and key points. Do not add your insights or rephrases the lines. Create outlines following this exact sample format for a section of a given article:

Input text:
It's Dangerous
The narrow, razor-thin paths with thousand-foot drop-offs on both sides aren't just challenging—they're potentially fatal. Hikers must navigate chains bolted into solid rock, with nothing between you and a catastrophic fall except your own grip strength and mental fortitude. The trail is so treacherous that the National Park Service has installed warning signs that say: "Since 2004, six people have died falling from cliffs on this route." As of 2024, there have been 18 confirmed deaths in and near Angel's Landing, not to mention the countless injuries sustained by hikers. That's why before you go, you need to be realistic about how dangerous Angel's Landing can be and whether you can handle it.

Output format:
It's Dangerous
-- Narrow razor-thin paths
-- Thousand-foot drop-offs
-- Requires clinging to chains bolted into rocks
-- No barriers
-- National Park Service warning sign says "Since 2004, six people have died falling from cliffs on this route."
-- 18 confirmed deaths near Angel's Landing by 2024
-- Numerous injuries"""},
                {"role": "user", "content": f"Create an outline from this text following the exact format shown:\n\n{text}"}
            ],
            temperature=0.1
        )
        return response.choices[0].message['content']
    except Exception as e:
        return str(e)

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
            outline_text = create_outline(content)
            
            title = os.path.splitext(file.filename)[0]
            results.append({
                'filename': file.filename,
                'title': title,
                'outline_text': outline_text
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
