from flask import Flask, request, jsonify, render_template, session
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import os
import uuid
from dotenv import load_dotenv, find_dotenv

# Load API key from .env file
_ = load_dotenv(find_dotenv())
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Flask app setup
app = Flask(__name__)
app.secret_key = "supersecretkey123"  # needed for sessions

# Database setup (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
db = SQLAlchemy(app)

# ChatMessage model (table)
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100))  # unique per user
    sender = db.Column(db.String(10))       # 'user' or 'ai'
    text = db.Column(db.Text)

# Create the database tables
with app.app_context():
    db.create_all()

# Helper: get session ID (unique per user)
def get_session_id():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())  # random unique ID
    return session["session_id"]

# Home route - load only this user's chat history
@app.route("/")
def home():
    sid = get_session_id()
    messages = ChatMessage.query.filter_by(session_id=sid).all()
    return render_template("index.html", messages=messages)

# Predict route - handle user input
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    user_input = data["text"]
    sid = get_session_id()

    # Save user message
    user_msg = ChatMessage(session_id=sid, sender="user", text=user_input)
    db.session.add(user_msg)
    db.session.commit()

    # Get AI response from OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_input}]
    )
    result = response.choices[0].message.content

    # Save AI message
    ai_msg = ChatMessage(session_id=sid, sender="ai", text=result)
    db.session.add(ai_msg)
    db.session.commit()

    return jsonify({"result": result})

# Clear chat route (only clears THIS user's chat)
@app.route("/clear", methods=["POST"])
def clear_chat():
    sid = get_session_id()
    ChatMessage.query.filter_by(session_id=sid).delete()
    db.session.commit()
    return jsonify({"status": "cleared"})

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)





