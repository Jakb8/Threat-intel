#!/usr/bin/env python3
"""
===============================================================================
 AGENT IA DE THREAT INTELLIGENCE
 Module : IA Générative - Projet Agents IA
===============================================================================

Cet agent répond à une exigence clé du projet : AGIR et non seulement répondre.

Comportement de l'agent (cf. cahier des charges, section 3.1) :
    1. Analyse la requête utilisateur (langage naturel)
    2. Détermine si un tool est nécessaire
    3. Sélectionne le(s) tool(s) approprié(s)
    4. Exécute l'action (appel d'outil interne et/ou externe)
    5. Intègre le résultat dans une réponse finale cohérente

Architecture :
    - Tool interne (fonction)  : detect_indicator()  -> identifie IP / domaine / hash
    - Tool interne (fonction)  : resolve_domain()      -> résolution DNS (A record)
    - Tool externe (API)       : check_abuseipdb()      -> réputation IP (AbuseIPDB)
    - Orchestrateur            : Agent.run()             -> logique de décision (raisonnement)
    - Contexte structuré       : AgentContext            -> principe inspiré du MCP
                                  (state partagé entre les étapes du raisonnement)

Auteur : Yacoub Bechi
===============================================================================
"""

import re
import json
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

import requests


# ──────────────────────────────────────────────────────────────────────────
#  CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────

# Récupère ta clé gratuite sur https://www.abuseipdb.com/account/api
ABUSEIPDB_API_KEY = "b277b470f40a843ba801036b26a17307b65236fb6a481d665995dfac31554bdd08eeeb5dd43835fe"
ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"

REQUEST_TIMEOUT = 8  # secondes


# ──────────────────────────────────────────────────────────────────────────
#  CONTEXTE STRUCTURÉ (principe MCP : Model Context Protocol)
# ──────────────────────────────────────────────────────────────────────────
# Le MCP encourage à structurer explicitement le contexte transmis au modèle
# plutôt que de tout mélanger dans un seul prompt. Ici, on matérialise ce
# principe avec un objet de contexte qui trace tout le raisonnement de
# l'agent : requête initiale, indicateur détecté, outils appelés, résultats,
# et erreurs rencontrées. Cet objet pourra être loggé ou affiché pour
# expliquer les décisions de l'agent (exigence 5.1).

@dataclass
class AgentContext:
    user_query: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    indicator_type: Optional[str] = None       # "ip" | "domain" | "hash" | None
    indicator_value: Optional[str] = None
    reasoning_steps: List[str] = field(default_factory=list)
    tool_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def log_step(self, step: str):
        """Trace une étape de raisonnement (utile pour expliquer les décisions)."""
        self.reasoning_steps.append(step)
        print(f"  🧠 {step}")

    def log_error(self, error: str):
        self.errors.append(error)
        print(f"  ⚠️  {error}")

    def to_dict(self) -> dict:
        return {
            "user_query": self.user_query,
            "timestamp": self.timestamp,
            "indicator_type": self.indicator_type,
            "indicator_value": self.indicator_value,
            "reasoning_steps": self.reasoning_steps,
            "tool_results": self.tool_results,
            "errors": self.errors,
        }


# ──────────────────────────────────────────────────────────────────────────
#  TOOL INTERNE #1 : Détection du type d'indicateur (fonction Python)
# ──────────────────────────────────────────────────────────────────────────

IP_REGEX = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
DOMAIN_REGEX = re.compile(r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b")
MD5_REGEX = re.compile(r"\b[a-fA-F0-9]{32}\b")
SHA256_REGEX = re.compile(r"\b[a-fA-F0-9]{64}\b")


def detect_indicator(text: str) -> Dict[str, Optional[str]]:
    """
    Tool interne #1.
    Analyse un texte libre et détecte le premier indicateur de compromission
    (IOC) reconnu : adresse IP, hash de fichier (MD5/SHA256), ou nom de domaine.

    Retourne un dict {"type": ..., "value": ...} ou {"type": None, "value": None}
    si rien n'est détecté.
    """
    sha256_match = SHA256_REGEX.search(text)
    if sha256_match:
        return {"type": "hash_sha256", "value": sha256_match.group()}

    md5_match = MD5_REGEX.search(text)
    if md5_match:
        return {"type": "hash_md5", "value": md5_match.group()}

    ip_match = IP_REGEX.search(text)
    if ip_match:
        # Validation simple : chaque octet doit être <= 255
        octets = ip_match.group().split(".")
        if all(0 <= int(o) <= 255 for o in octets):
            return {"type": "ip", "value": ip_match.group()}

    domain_match = DOMAIN_REGEX.search(text)
    if domain_match:
        return {"type": "domain", "value": domain_match.group()}

    return {"type": None, "value": None}


# ──────────────────────────────────────────────────────────────────────────
#  TOOL INTERNE #2 : Résolution DNS (fonction Python)
# ──────────────────────────────────────────────────────────────────────────

def resolve_domain(domain: str) -> Dict[str, Any]:
    """
    Tool interne #2.
    Résout un nom de domaine en adresse IP (enregistrement A).
    Permet de chaîner domaine -> IP -> vérification de réputation.
    """
    try:
        ip = socket.gethostbyname(domain)
        return {"success": True, "ip": ip}
    except socket.gaierror as e:
        return {"success": False, "error": f"Résolution DNS échouée : {e}"}


# ──────────────────────────────────────────────────────────────────────────
#  TOOL EXTERNE : Vérification de réputation via l'API AbuseIPDB
# ──────────────────────────────────────────────────────────────────────────

def check_abuseipdb(ip: str) -> Dict[str, Any]:
    """
    Tool externe (API).
    Interroge l'API publique AbuseIPDB pour obtenir le score de réputation
    d'une adresse IP (nombre de signalements, score de confiance d'abus, pays...).

    Documentation API : https://docs.abuseipdb.com/
    """
    headers = {
        "Key": ABUSEIPDB_API_KEY,
        "Accept": "application/json",
    }
    params = {
        "ipAddress": ip,
        "maxAgeInDays": 90,
    }

    try:
        response = requests.get(
            ABUSEIPDB_URL,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 401:
            return {"success": False, "error": "Clé API AbuseIPDB invalide ou manquante."}

        if response.status_code == 429:
            return {"success": False, "error": "Quota API AbuseIPDB dépassé. Réessaie plus tard."}

        response.raise_for_status()
        data = response.json().get("data", {})

        return {
            "success": True,
            "ip": data.get("ipAddress"),
            "abuse_score": data.get("abuseConfidenceScore"),  # 0-100
            "country": data.get("countryCode"),
            "isp": data.get("isp"),
            "total_reports": data.get("totalReports"),
            "is_whitelisted": data.get("isWhitelisted"),
            "last_reported": data.get("lastReportedAt"),
        }

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout : l'API AbuseIPDB n'a pas répondu à temps."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Erreur de connexion réseau vers AbuseIPDB."}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Erreur API inattendue : {e}"}


# ──────────────────────────────────────────────────────────────────────────
#  ORCHESTRATEUR / AGENT
# ──────────────────────────────────────────────────────────────────────────

class ThreatIntelAgent:
    """
    Agent IA de Threat Intelligence.

    Implémente la boucle de raisonnement demandée par le cahier des charges :
        analyse -> décision -> sélection de tool -> exécution -> synthèse
    """

    def __init__(self):
        self.name = "ThreatIntelAgent"

    def run(self, user_query: str) -> AgentContext:
        ctx = AgentContext(user_query=user_query)

        print(f"\n{'='*70}")
        print(f"  🤖 {self.name} — Requête reçue : \"{user_query}\"")
        print(f"{'='*70}")

        # ── ÉTAPE 1 : Analyse de la requête ──────────────────────────────
        ctx.log_step("Analyse de la requête utilisateur pour détecter un indicateur (IOC)...")
        detection = detect_indicator(user_query)
        ctx.indicator_type = detection["type"]
        ctx.indicator_value = detection["value"]

        if ctx.indicator_type is None:
            ctx.log_error("Aucun indicateur (IP / domaine / hash) détecté dans la requête.")
            return ctx

        ctx.log_step(f"Indicateur détecté -> type='{ctx.indicator_type}', valeur='{ctx.indicator_value}'")

        # ── ÉTAPE 2 : Décision -> sélection du tool ──────────────────────
        if ctx.indicator_type == "ip":
            ctx.log_step("Décision : indicateur de type IP -> appel direct du tool AbuseIPDB.")
            self._check_ip_reputation(ctx, ctx.indicator_value)

        elif ctx.indicator_type == "domain":
            ctx.log_step("Décision : indicateur de type domaine -> résolution DNS nécessaire avant vérification.")
            dns_result = resolve_domain(ctx.indicator_value)
            ctx.tool_results["dns_resolution"] = dns_result

            if dns_result["success"]:
                resolved_ip = dns_result["ip"]
                ctx.log_step(f"Domaine résolu en IP '{resolved_ip}' -> appel du tool AbuseIPDB sur cette IP.")
                self._check_ip_reputation(ctx, resolved_ip)
            else:
                ctx.log_error(dns_result["error"])

        elif ctx.indicator_type in ("hash_md5", "hash_sha256"):
            ctx.log_step("Décision : indicateur de type hash -> hors périmètre AbuseIPDB (réservé aux IP).")
            ctx.tool_results["note"] = (
                "Les hashs de fichiers nécessitent un service dédié (ex. VirusTotal). "
                "Non couvert par cette version de l'agent."
            )

        # ── ÉTAPE 3 : Synthèse de la réponse finale ──────────────────────
        ctx.log_step("Synthèse de la réponse finale à partir des résultats des tools.")
        self._print_final_report(ctx)

        return ctx

    def _check_ip_reputation(self, ctx: AgentContext, ip: str):
        """Exécute le tool externe AbuseIPDB et stocke le résultat dans le contexte."""
        result = check_abuseipdb(ip)
        ctx.tool_results["abuseipdb"] = result

        if not result["success"]:
            ctx.log_error(result["error"])

    def _print_final_report(self, ctx: AgentContext):
        print(f"\n{'─'*70}")
        print("  📋 RAPPORT FINAL")
        print(f"{'─'*70}")

        abuse_data = ctx.tool_results.get("abuseipdb")

        if not abuse_data:
            print("  Aucune donnée de réputation disponible.")
            print(f"{'='*70}\n")
            return

        if not abuse_data.get("success"):
            print(f"  ❌ Impossible d'obtenir le verdict : {abuse_data.get('error')}")
            print(f"{'='*70}\n")
            return

        score = abuse_data["abuse_score"]

        if score >= 75:
            verdict = "🔴 RISQUE ÉLEVÉ"
        elif score >= 25:
            verdict = "🟠 RISQUE MOYEN"
        else:
            verdict = "🟢 RISQUE FAIBLE"

        print(f"  IP analysée        : {abuse_data['ip']}")
        print(f"  Verdict             : {verdict}  (score de confiance d'abus : {score}/100)")
        print(f"  Pays                : {abuse_data.get('country', 'Inconnu')}")
        print(f"  FAI / Organisation  : {abuse_data.get('isp', 'Inconnu')}")
        print(f"  Nombre de rapports  : {abuse_data.get('total_reports', 0)}")
        print(f"  Liste blanche       : {'Oui' if abuse_data.get('is_whitelisted') else 'Non'}")
        print(f"{'='*70}\n")


# ──────────────────────────────────────────────────────────────────────────
#  POINT D'ENTRÉE — Mode interactif CLI
# ──────────────────────────────────────────────────────────────────────────

def main():
    agent = ThreatIntelAgent()

    print("\n" + "═" * 70)
    print("  AGENT IA DE THREAT INTELLIGENCE — Mode interactif")
    print("  Exemples de requêtes :")
    print("    - 'Cette IP 185.220.101.45 est-elle suspecte ?'")
    print("    - 'Vérifie la réputation de google.com'")
    print("  Tape 'exit' pour quitter.")
    print("═" * 70)

    while True:
        query = input("\n💬 Ta requête > ").strip()
        if query.lower() in ("exit", "quit", "q"):
            print("Fin de session. À bientôt !")
            break
        if not query:
            continue

        ctx = agent.run(query)

        # Optionnel : sauvegarder le contexte structuré (façon MCP) en JSON
        # pour analyse ou pour alimenter un rapport de tests.
        # with open("last_context.json", "w") as f:
        #     json.dump(ctx.to_dict(), f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
