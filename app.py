from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq
import requests
import os
import ipaddress

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
CORS(app)

# Chargement des clés API
ABUSE_API_KEY = os.getenv("ABUSE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Vérification des clés
if not ABUSE_API_KEY:
    raise ValueError("ABUSE_API_KEY introuvable dans le fichier .env")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY introuvable dans le fichier .env")

# Client Groq
groq_client = Groq(api_key=GROQ_API_KEY)


@app.route('/')
def home():
    return "CyberShield API is running"


@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "errors": ["Aucune donnée reçue."]
            }), 400

        indicator = data.get("query", "").strip()

        if not indicator:
            return jsonify({
                "errors": ["Veuillez saisir une adresse IP."]
            }), 400

        # Vérifier que c'est bien une IP
        try:
            ipaddress.ip_address(indicator)
        except ValueError:
            return jsonify({
                "errors": [
                    "AbuseIPDB supporte uniquement les adresses IP."
                ]
            }), 400

        # ------------------------
        # Appel AbuseIPDB
        # ------------------------
        headers = {
            "Key": ABUSE_API_KEY,
            "Accept": "application/json"
        }

        params = {
            "ipAddress": indicator,
            "maxAgeInDays": 90
        }

        response = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            headers=headers,
            params=params,
            timeout=20
        )

        print("ABUSE STATUS :", response.status_code)
        print("ABUSE RESPONSE :", response.text)

        if not response.ok:
            return jsonify({
                "errors": [
                    f"Erreur AbuseIPDB ({response.status_code})",
                    response.text
                ]
            }), response.status_code

        result = response.json().get("data", {})

        score = result.get("abuseConfidenceScore", 0)
        reports = result.get("totalReports", 0)
        country = result.get("countryCode", "Unknown")
        isp = result.get("isp", "Unknown")

        abuse_data = {
            "ip": indicator,
            "country": country,
            "isp": isp,
            "total_reports": reports,
            "score": score,
            "is_whitelisted":
                result.get("isWhitelisted", False),
            "usage_type":
                result.get("usageType", "Unknown"),
            "domain":
                result.get("domain", "Unknown")
        }

        # ------------------------
        # Calcul du risque
        # ------------------------
        if score >= 75:
            level = "high"
            label = "Risque élevé"

        elif score >= 40:
            level = "medium"
            label = "Risque moyen"

        else:
            level = "low"
            label = "Faible risque"

        verdict = {
            "level": level,
            "label": label,
            "score": score
        }

        reasoning_steps = [
            f"IP analysée : {indicator}",
            f"Pays : {country}",
            f"Fournisseur : {isp}",
            f"Nombre de signalements : {reports}",
            f"Score de confiance : {score}/100",
            f"Niveau de risque : {label}"
        ]

        # ------------------------
        # Analyse IA avec Groq
        # ------------------------
        prompt = f"""
Tu es un analyste SOC spécialisé en Threat Intelligence.

Adresse IP : {indicator}
Pays : {country}
Fournisseur : {isp}
Nombre de signalements : {reports}
Score d'abus : {score}/100
Niveau de risque : {label}

Produis :

1. Une explication du risque.
2. Les menaces potentielles.
3. Les actions de remédiation.
4. Une conclusion courte.
"""

        llm_analysis = ""

        try:
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content":
                            "Tu es un expert SOC et Threat Intelligence."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=700
            )

            llm_analysis = (
                completion
                .choices[0]
                .message
                .content
            )

        except Exception as e:
            llm_analysis = (
                f"Erreur Groq : {str(e)}"
            )

        # ------------------------
        # Réponse finale
        # ------------------------
        return jsonify({
            "reasoning_steps": reasoning_steps,
            "verdict": verdict,
            "abuse_data": abuse_data,
            "llm_analysis": llm_analysis,
            "errors": []
        })

    except Exception as e:
        return jsonify({
            "errors": [str(e)]
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )