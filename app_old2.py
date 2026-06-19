from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return 'CyberShield API is running'

@app.route('/api/analyze', methods=['POST'])
def analyze():

    data = request.get_json()
    query = data.get('query', '')

    return jsonify({
        "reasoning_steps": [
            f"Analyse de : {query}",
            "Interrogation des sources",
            "Calcul du score"
        ],
        "verdict": {
            "level": "low",
            "label": "Faible risque",
            "score": 15
        },
        "abuse_data": {
            "ip": "1.1.1.1",
            "country": "Australia",
            "isp": "Cloudflare",
            "total_reports": 0,
            "is_whitelisted": True
        },
        "errors": []
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
