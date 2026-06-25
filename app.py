import re
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import analyze_threats

try:
    from rag import RAGSystem
    RAG_AVAILABLE = True
except Exception:
    RAG_AVAILABLE = False

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

ABUSEIPDB_API_KEY = "b277b470f40a843ba801036b26a17307b65236fb6a481d665995dfac31554bdd08eeeb5dd43835fe"
VIRUSTOTAL_API_KEY = "f27563ff4fbf260f20f5c12880851bb9a2b6dc4f1cd5ed9ef76414d788e46021"

ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"
VT_URL = "https://www.virustotal.com/api/v3/domains/"

IP_REGEX = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
DOMAIN_REGEX = r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b'


@app.route("/")
def home():
    return "THREAT INTEL API RUNNING"


def extract_iocs(text):
    return {
        "ips": list(set(re.findall(IP_REGEX, text))),
        "emails": list(set(re.findall(EMAIL_REGEX, text))),
        "domains": list(set(re.findall(DOMAIN_REGEX, text)))
    }


def check_ip_abuse(ip):
    headers = {"Key": ABUSEIPDB_API_KEY, "Accept": "application/json"}
    params = {"ipAddress": ip, "maxAgeInDays": 90}
    try:
        r = requests.get(ABUSEIPDB_URL, headers=headers, params=params)
        return r.json()
    except Exception as e:
        return {"error": str(e), "ip": ip}


def check_domain(domain):
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    try:
        r = requests.get(VT_URL + domain, headers=headers)
        return r.json()
    except Exception as e:
        return {"error": str(e), "domain": domain}


def calculate_score(ip_results):
    score = 0
    for r in ip_results:
        try:
            if "data" in r:
                score = max(score, r["data"]["abuseConfidenceScore"])
        except:
            pass
    return min(score, 100)


def analyze_iocs(iocs):
    ip_results = []
    domain_results = []

    for ip in iocs["ips"]:
        ip_results.append(check_ip_abuse(ip))

    for domain in iocs["domains"]:
        domain_results.append(check_domain(domain))

    threat_data = {
        "score": calculate_score(ip_results),
        "ips": ip_results,
        "domains": domain_results,
        "iocs": iocs
    }

    llm_analysis = analyze_threats(threat_data)

    return {
        "iocs": iocs,
        "analysis": threat_data,
        "llm_analysis": llm_analysis
    }


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    text = data.get("text", "")
    iocs = extract_iocs(text)
    result = analyze_iocs(iocs)
    return jsonify(result)


rag_system = None
if RAG_AVAILABLE:
    EMBEDDINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rag_embeddings.json")
    try:
        rag_system = RAGSystem()
        if os.path.exists(EMBEDDINGS_FILE):
            rag_system.load_index()
            print(f"RAG pret: {len(rag_system.chunks)} chunks indexes")
        else:
            print("RAG : index non trouve. Lance d'abord python3 rag.py")
    except Exception as e:
        print(f"RAG non disponible: {e}")
        rag_system = None


@app.route("/rag", methods=["POST"])
def rag_query():
    if rag_system is None:
        return jsonify({"error": "RAG non disponible"}), 503
    data = request.get_json()
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Requete vide"}), 400
    try:
        results = rag_system.retrieve(query)
        docs = [
            {"source": c.source, "page": c.page, "text": c.text[:300], "score": s}
            for c, s in zip(results.chunks, results.scores)
        ]
        response = rag_system.generate(query)
        return jsonify({"query": query, "documents": docs, "response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
