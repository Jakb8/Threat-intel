#!/usr/bin/env python3
"""
===============================================================================
 BACKEND FLASK — Agent IA de Threat Intelligence
===============================================================================

Ce serveur expose l'agent existant (ThreatIntelAgent) via une API REST,
pour qu'une page web (frontend.html) puisse l'interroger.

Endpoint principal :
    POST /api/analyze
    Body JSON : { "query": "Cette IP 185.220.101.45 est-elle suspecte ?" }
    Réponse   : le contexte complet de raisonnement de l'agent (JSON)

Lancement :
    pip install flask flask-cors requests
    python app.py
    -> ouvre http://localhost:5000 dans ton navigateur
===============================================================================
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from groq import Groq
import os

client = Groq(
    api_key=os.environ.get("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")
)

# On réutilise directement la logique de l'agent, sans rien dupliquer.
from agent import ThreatIntelAgent

app = Flask(__name__, static_folder=".")
CORS(app)  # autorise les appels depuis le frontend (utile en dev local)

agent = ThreatIntelAgent()


@app.route("/")
def index():
    """Sert directement la page frontend pour un lancement en un seul clic."""
    return send_from_directory(".", "frontend.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Reçoit une requête utilisateur, exécute l'agent, et retourne
    le contexte de raisonnement complet (étapes, tool utilisés, verdict).
    """
    body = request.get_json(silent=True) or {}
    user_query = (body.get("query") or "").strip()

    if not user_query:
        return jsonify({"error": "Le champ 'query' est requis."}), 400

    try:
        ctx = agent.run(user_query)
        return jsonify(build_response(ctx))
    except Exception as e:
        # Garde-fou global : l'agent ne doit jamais planter le serveur.
        return jsonify({"error": f"Erreur interne de l'agent : {e}"}), 500


def build_response(ctx) -> dict:
    """
    Transforme le contexte de l'agent en une réponse JSON exploitable
    par le frontend, avec un verdict pré-calculé pour l'affichage.
    """
    data = ctx.to_dict()

    abuse_data = ctx.tool_results.get("abuseipdb")
    verdict = None

    if abuse_data and abuse_data.get("success"):
        score = abuse_data["abuse_score"]
        if score >= 75:
            verdict = {"level": "high", "label": "Risque élevé", "score": score}
        elif score >= 25:
            verdict = {"level": "medium", "label": "Risque moyen", "score": score}
        else:
            verdict = {"level": "low", "label": "Risque faible", "score": score}

    data["verdict"] = verdict
    data["abuse_data"] = abuse_data
    return data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
