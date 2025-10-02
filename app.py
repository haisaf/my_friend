from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv

# Load API key from .env file
_ = load_dotenv(find_dotenv())
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Flask app setup
app = Flask(__name__)

# Database setup (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
db = SQLAlchemy(app)

# ChatMessage model (table)
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(10))  # 'user' or 'ai'
    text = db.Column(db.Text)

# Create the database tables (only runs once if not created already)
with app.app_context():
    db.create_all()

# Home route - load chat history
@app.route("/")
def home():
    messages = ChatMessage.query.all()
    return render_template("index.html", messages=messages)

# Predict route - handle user input
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    user_input = data["text"]

    # Save user message
    user_msg = ChatMessage(sender="user", text=user_input)
    db.session.add(user_msg)
    db.session.commit()

    # Get AI response from OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_input}]
    )
    result = response.choices[0].message.content

    # Save AI message
    ai_msg = ChatMessage(sender="ai", text=result)
    db.session.add(ai_msg)
    db.session.commit()

    return jsonify({"result": result})

# Clear chat route
@app.route("/clear", methods=["POST"])
def clear_chat():
    ChatMessage.query.delete()
    db.session.commit()
    return jsonify({"status": "cleared"})

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)



