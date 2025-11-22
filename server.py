# server.py
import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from google import genai as gemini # <-- পরিবর্তন ১: জেমিনি SDK-কে 'gemini' নামে ইমপোর্ট করা হলো
import base64

load_dotenv()

app = Flask(__name__, template_folder='.') 
# Configuration
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# <-- পরিবর্তন ২: Client ইনিশিয়ালাইজেশন
# এখন genai.configure() এর বদলে API Key ব্যবহার করে সরাসরি ক্লায়েন্ট অবজেক্ট তৈরি করা হলো
client = gemini.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Simple in-memory knowledge base (Simulating RAG storage for demonstration)
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
    # Simple check for password sent via form data
    if request.form.get('admin_pass') != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized Access"}), 401

    text_input = request.form.get('text_input')
    uploaded_file = request.files.get('file')

    if not text_input and not uploaded_file:
        return jsonify({"error": "No content provided."}), 400

    global knowledge_base

    if uploaded_file:
        try:
            # Create a Part from the uploaded image file
            image_part = gemini.types.Part.from_bytes( # <-- পরিবর্তন ৩: gemini.types.Part ব্যবহার
                data=uploaded_file.read(),
                mime_type=uploaded_file.content_type
            )
            
            # Prompt to instruct the model to learn from the image
            prompt = (
                "The following image contains a mathematical or physics concept, formula, "
                "or problem from an HSC-level textbook. Analyze it, summarize the key information, "
                "and integrate this knowledge into your base to solve future user questions. "
                "Confirm learning with the message: 'New content added to knowledge base from image.'"
            )
            
            # Send the image and prompt to the model
            response = client.models.generate_content([prompt, image_part]) # <-- পরিবর্তন ৪: client.models.generate_content ব্যবহার
            
            # Append the summary/learning to our simple knowledge base
            knowledge_base.append(f"Learned from image summary: {response.text}")

            return jsonify({"success": True, "message": f"Successfully learned from image. Model response: {response.text}"})

        except Exception as e:
            return jsonify({"error": f"Error learning from image: {str(e)}"}), 500

    if text_input:
        # For text, we directly add it to the knowledge base
        knowledge_base.append(f"Learned from text: {text_input}")
        return jsonify({"success": True, "message": "Learned from text successfully."})

# --- User (Question) Endpoint ---

@app.route('/ask', methods=['POST'])
def ask_ai():
    """Endpoint for users to ask math/physics questions."""
    data = request.json
    question = data.get('question')

    if not question:
        return jsonify({"error": "No question provided."}), 400

    # Retrieve knowledge and add it to the prompt (RAG Simulation)
    context = "\n".join(knowledge_base)
    
    # The main prompt for the AI Tutor
    full_prompt = (
        f"You are an HSC-level Math and Physics Tutor for students in Bangladesh. "
        f"You have the following supplementary information from textbooks/notes that you MUST use to answer the question: \n---Knowledge Base---\n{context}\n---\n"
        f"Now, provide a detailed and accurate solution to the question below. Respond in Bengali (Bangla) for the user's ease of understanding. "
        f"Question: {question}"
    )

    try:
        # Generate content using the context and the user's question
        response = client.models.generate_content(full_prompt) # <-- পরিবর্তন ৪: client.models.generate_content ব্যবহার
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
    # Use a port that Render/other services expect (e.g., 5000 or the one set by environment)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
