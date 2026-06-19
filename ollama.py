import ollama

prompt = f"""
IP : {ip}
Score AbuseIPDB : {score}
Pays : {country}
FAI : {isp}

Explique le risque et donne des recommandations.
"""

response = ollama.chat(
    model='llama3',
    messages=[
        {"role": "user", "content": prompt}
    ]
)

analysis = response["message"]["content"]
