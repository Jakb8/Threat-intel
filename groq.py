import requests
import json

GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Tu es un analyste en cybersecurite expert. Tu recois des donnees de Threat Intelligence (reputation IP, domaines, score de risque) et tu produis une analyse claire et actionable en francais.

Structure ta reponse en 3 parties :
1. **Resume** — synthese du niveau de risque global
2. **Analyse detaillee** — interpretation des indicateurs suspects
3. **Recommandations** — actions concretes a prendre

Sois concis, technique et precis. Utilise du texte structure (pas de JSON)."""


def groq_chat(messages, temperature=0.3, max_tokens=1024):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erreur d'analyse LLM : {e}"


def analyze_threats(threat_data: dict) -> str:
    user_prompt = f"""Analyse ces données de Threat Intelligence :

Score de risque : {threat_data.get('score', '?')}/100

IPs analysées :
{json.dumps(threat_data.get('ips', []), indent=2, ensure_ascii=False)}

Domaines analysés :
{json.dumps(threat_data.get('domains', []), indent=2, ensure_ascii=False)}

IOCs détectés :
{json.dumps(threat_data.get('iocs', {}), indent=2, ensure_ascii=False)}
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    return groq_chat(messages)
