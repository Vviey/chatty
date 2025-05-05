from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["https://staging4.bitcoiners.africa"])

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

print(">>> Loaded API Key:", bool(DEEPSEEK_API_KEY))

def fetch_site_text(url="https://staging4.bitcoiners.africa/"):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # Extract visible content
        visible_elements = soup.find_all(["p", "li", "h1", "h2", "h3"])
        text = " ".join(el.get_text().strip() for el in visible_elements if el.get_text().strip())

        return text[:2000]  # Limit to ~2000 chars for prompt size
    except Exception as e:
        print("Error fetching site content:", e)
        return ""


@app.route('/', methods=['GET'])
def home():
    return "Am alive!!"



@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message')

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        if not DEEPSEEK_API_KEY:
            return jsonify({"error": "Missing DeepSeek API key"}), 500

        site_context = fetch_site_text()

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": f"You are a chatbot for Bitcoiners Africa. Use the following website content to answer questions:\n\n{site_context}"
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        bot_reply = response.json()['choices'][0]['message']['content']
        return jsonify({"reply": bot_reply})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print(">>> Flask app starting...")
    app.run(debug=True, port=5000)
