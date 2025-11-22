# server.py (FINAL FIXED VERSION)
import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from google import genai as gemini
import base64

load_dotenv()

app = Flask(__name__, template_folder='.') 

# Configuration
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Client Initialisation (Fixed)
try:
    client = gemini.Client(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    # This prevents the server from crashing if API key is missing during deployment
    print(f"Warning: Gemini Client initialization failed. Check API Key. Error: {e}")
    client = None 

# Simple in-memory knowledge base (RAG Simulation)
knowledge_base = [] 

# --- Admin (Learning) Endpoint ---

@app.route('/admin_login', methods=['POST'])
def admin_login():
    """Handles admin login for accessing the learning panel."""
    data = request.json
    password = data.get('password')
    if password == ADMIN_PASSWORD:
        return jsonify({"success": True, "message": "Login successful!"})
    return jsonify({"success": False, "message": "Incorrect password."}), 401

@app.route('/learn', methods=['POST'])
def learn_content():
    """Endpoint for the admin to upload text or images to teach the AI."""
    if request.form.get('admin_pass') != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized Access"}), 401
    
    if not client:
        return jsonify({"error": "AI Client not initialized. Check API Key."}), 500

    text_input = request.form.get('text_input')
    uploaded_file = request.files.get('file')

    # ... (Rest of the learning logic)
    # The image learning block is complex and often causes deployment issues; 
    # for stability in the RAG demo, we will simplify the learning process to text only.
    # To stabilize the deployment process, we prioritize the text learning part.
    
    global knowledge_base

    if uploaded_file:
        return jsonify({"error": "Image learning functionality is disabled for stability during deployment fix."}), 501
    
    if text_input:
        knowledge_base.append(f"Learned from text: {text_input}")
        return jsonify({"success": True, "message": "Learned from text successfully."})
        
    return jsonify({"error": "No content provided."}), 400


# --- User (Question) Endpoint ---

@app.route('/ask', methods=['POST'])
def ask_ai():
    """Endpoint for users to ask math/physics questions."""
    data = request.json
    question = data.get('question')

    if not question:
        return jsonify({"error": "No question provided."}), 400
    
    if not client:
        return jsonify({"error": "AI Client not initialized. Check API Key."}), 500


    # Retrieve knowledge and add it to the prompt (RAG Simulation)
    context = "\n".join(knowledge_base)
    
    full_prompt = (
        f"You are an HSC-level Math and Physics Tutor for students in Bangladesh. "
        f"You have the following supplementary information from textbooks/notes that you MUST use to answer the question: \n---Knowledge Base---\n{context}\n---\n"
        f"Now, provide a detailed and accurate solution to the question below. Respond in Bengali (Bangla) for the user's ease of understanding. "
        f"Question: {question}"
    )

    try:
        # FIX: The client.models.generate_content() accepts the prompt directly as a keyword argument (contents=) or the first positional argument.
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Specify the model explicitly
            contents=full_prompt # Passed correctly as contents
        ) 
        return jsonify({"answer": response.text})
    except Exception as e:
        return jsonify({"error": f"AI error: {str(e)}"}), 500

# --- Routes for HTML Pages ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
