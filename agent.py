#!/usr/bin/env python3
import re
import json
import socket
import readline
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

import requests
from groq import analyze_threats, groq_chat, SYSTEM_PROMPT

ABUSEIPDB_API_KEY = "b277b470f40a843ba801036b26a17307b65236fb6a481d665995dfac31554bdd08eeeb5dd43835fe"
ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"
REQUEST_TIMEOUT = 8
MAX_MEMORY = 10


MCP_SYSTEM_PROMPT = """Tu es un agent de Threat Intelligence suivant le Model Context Protocol (MCP).

CONTEXTE :
- Tu reçois une requête utilisateur contenant potentiellement des IOCs (IP, domaine, hash).
- Tu disposes d'outils (AbuseIPDB, résolution DNS, analyse LLM) et d'une mémoire des interactions précédentes.
- Tu dois décider quels outils utiliser et dans quel ordre.

SCHEMA DE DECISION :
1. Analyser la requête -> identifier le type d'indicateur
2. Déterminer les outils nécessaires (check_ip, resolve_domain, llm_analysis)
3. Exécuter les outils dans l'ordre approprié
4. Synthétiser les résultats avec le LLM
5. Retourner une réponse structurée (Résumé, Analyse, Recommandations)

MEMOIRE :
Les interactions précédentes sont fournies. Tu peux t'y référer si l'utilisateur fait référence à une analyse passée.

Réponds en français, de manière structurée et technique."""


@dataclass
class MemoryEntry:
    query: str
    indicator_type: Optional[str]
    indicator_value: Optional[str]
    score: Optional[int]
    summary: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentContext:
    user_query: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    indicator_type: Optional[str] = None
    indicator_value: Optional[str] = None
    reasoning_steps: List[str] = field(default_factory=list)
    tool_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    llm_response: Optional[str] = None
    memory_context: str = ""

    def log_step(self, step: str):
        self.reasoning_steps.append(step)
        print(f"  -> {step}")

    def log_error(self, error: str):
        self.errors.append(error)
        print(f"  !! {error}")

    def to_dict(self) -> dict:
        return {
            "user_query": self.user_query,
            "timestamp": self.timestamp,
            "indicator_type": self.indicator_type,
            "indicator_value": self.indicator_value,
            "reasoning_steps": self.reasoning_steps,
            "tool_results": self.tool_results,
            "errors": self.errors,
            "llm_response": self.llm_response,
        }


IP_REGEX = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
DOMAIN_REGEX = re.compile(r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b")
MD5_REGEX = re.compile(r"\b[a-fA-F0-9]{32}\b")
SHA256_REGEX = re.compile(r"\b[a-fA-F0-9]{64}\b")


def detect_indicator(text: str) -> Dict[str, Optional[str]]:
    sha256_match = SHA256_REGEX.search(text)
    if sha256_match:
        return {"type": "hash_sha256", "value": sha256_match.group()}

    md5_match = MD5_REGEX.search(text)
    if md5_match:
        return {"type": "hash_md5", "value": md5_match.group()}

    ip_match = IP_REGEX.search(text)
    if ip_match:
        octets = ip_match.group().split(".")
        if all(0 <= int(o) <= 255 for o in octets):
            return {"type": "ip", "value": ip_match.group()}

    domain_match = DOMAIN_REGEX.search(text)
    if domain_match:
        return {"type": "domain", "value": domain_match.group()}

    return {"type": None, "value": None}


def resolve_domain(domain: str) -> Dict[str, Any]:
    try:
        ip = socket.gethostbyname(domain)
        return {"success": True, "ip": ip}
    except socket.gaierror as e:
        return {"success": False, "error": f"Resolution DNS echouee : {e}"}


def check_abuseipdb(ip: str) -> Dict[str, Any]:
    headers = {"Key": ABUSEIPDB_API_KEY, "Accept": "application/json"}
    params = {"ipAddress": ip, "maxAgeInDays": 90}

    try:
        response = requests.get(ABUSEIPDB_URL, headers=headers, params=params, timeout=REQUEST_TIMEOUT)

        if response.status_code == 401:
            return {"success": False, "error": "Cle API AbuseIPDB invalide ou manquante."}
        if response.status_code == 429:
            return {"success": False, "error": "Quota API AbuseIPDB depasse. Reessaie plus tard."}

        response.raise_for_status()
        data = response.json().get("data", {})

        return {
            "success": True,
            "ip": data.get("ipAddress"),
            "abuse_score": data.get("abuseConfidenceScore"),
            "country": data.get("countryCode"),
            "isp": data.get("isp"),
            "total_reports": data.get("totalReports"),
            "is_whitelisted": data.get("isWhitelisted"),
            "last_reported": data.get("lastReportedAt"),
        }

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout : l'API AbuseIPDB n'a pas repondu a temps."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Erreur de connexion reseau vers AbuseIPDB."}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Erreur API inattendue : {e}"}


class ThreatIntelAgent:
    def __init__(self):
        self.name = "ThreatIntelAgent"
        self.memory: List[MemoryEntry] = []

    def _format_memory(self) -> str:
        if not self.memory:
            return "Aucune interaction precedente."
        lines = []
        for i, entry in enumerate(self.memory[-MAX_MEMORY:], 1):
            score_str = f"[Score: {entry.score}/100]" if entry.score is not None else ""
            itype = entry.indicator_type or "?"
            ivalue = entry.indicator_value or "?"
            lines.append(
                f"{i}. Requete: \"{entry.query}\" -> "
                f"{itype}: {ivalue} {score_str} "
                f"({entry.timestamp[:19]})"
            )
        return "\n".join(lines)

    def _build_mcp_context(self, query: str, detection: dict) -> str:
        memory_part = self._format_memory()
        return (
            f"[MCP CONTEXT]\n"
            f"Timestamp: {datetime.now().isoformat()}\n"
            f"Requete utilisateur: \"{query}\"\n"
            f"Indicateur detecte: type={detection['type']}, valeur={detection['value']}\n"
            f"\n[MEMOIRE SESSION]\n{memory_part}\n"
            f"\n[OUTILS DISPONIBLES]\n"
            f"- detect_indicator(text) -> type, valeur\n"
            f"- resolve_domain(domain) -> IP resolue\n"
            f"- check_abuseipdb(ip) -> score, pays, FAI, rapports\n"
            f"- analyze_threats(threat_data) -> analyse LLM structuree\n"
        )

    def _check_if_reference_to_past(self, query: str) -> Optional[MemoryEntry]:
        query_lower = query.lower()
        for entry in reversed(self.memory[-MAX_MEMORY:]):
            if entry.indicator_value and entry.indicator_value.lower() in query_lower:
                return entry
            for word in query_lower.split():
                if entry.indicator_value and entry.indicator_value.lower() == word:
                    return entry
        return None

    def run(self, user_query: str) -> AgentContext:
        ctx = AgentContext(user_query=user_query)

        print(f"\n{'='*70}")
        print(f"  AGENT {self.name} — Requete recue : \"{user_query}\"")
        print(f"{'='*70}")

        past_ref = self._check_if_reference_to_past(user_query)
        if past_ref:
            ctx.log_step(f"Reference a une analyse precedente : {past_ref.indicator_value} ({past_ref.timestamp[:19]})")
            ctx.memory_context = f"[MEMOIRE] Analyse precedente trouvee : {past_ref.indicator_value} -> {past_ref.summary[:200]}"

        ctx.log_step("[MCP] Analyse de la requete utilisateur pour detection d'IOC...")
        detection = detect_indicator(user_query)
        ctx.indicator_type = detection["type"]
        ctx.indicator_value = detection["value"]

        mcp_context = self._build_mcp_context(user_query, detection)
        ctx.log_step(f"[MCP] Contexte construit (memoire: {len(self.memory)} interactions)")

        if ctx.indicator_type is None:
            ctx.log_error("Aucun indicateur detecte dans la requete.")
            ctx.log_step("[MCP] Decision: aucun outil necessaire, reponse LLM seule")
            ctx.llm_response = groq_chat([
                {"role": "system", "content": MCP_SYSTEM_PROMPT + "\n\n" + mcp_context},
                {"role": "user", "content": user_query}
            ])
            return ctx

        ctx.log_step(f"[MCP] Indicateur detecte -> type='{ctx.indicator_type}', valeur='{ctx.indicator_value}'")

        if ctx.indicator_type == "ip":
            ctx.log_step("[MCP] Decision: utiliser l'outil check_abuseipdb() pour la reputation IP")
            self._check_ip_reputation(ctx, ctx.indicator_value)

        elif ctx.indicator_type == "domain":
            ctx.log_step("[MCP] Decision: utiliser l'outil resolve_domain() puis check_abuseipdb()")
            dns_result = resolve_domain(ctx.indicator_value)
            ctx.tool_results["dns_resolution"] = dns_result

            if dns_result["success"]:
                resolved_ip = dns_result["ip"]
                ctx.log_step(f"Domaine resolu en IP '{resolved_ip}' -> verification AbuseIPDB")
                self._check_ip_reputation(ctx, resolved_ip)
            else:
                ctx.log_error(dns_result["error"])

        elif ctx.indicator_type in ("hash_md5", "hash_sha256"):
            ctx.log_step("[MCP] Decision: hash detecte -> analyse LLM seule (pas d'API reputation pour hash)")
            ctx.tool_results["hash_type"] = ctx.indicator_type

        ctx.log_step("[MCP] Decision: utiliser l'outil analyze_threats() pour la synthese LLM")
        self._llm_analysis(ctx, mcp_context)

        score = None
        abuse = ctx.tool_results.get("abuseipdb", {})
        if abuse.get("success"):
            score = abuse.get("abuse_score")

        summary = (ctx.llm_response or "")[:150]
        self.memory.append(MemoryEntry(
            query=user_query,
            indicator_type=ctx.indicator_type,
            indicator_value=ctx.indicator_value,
            score=score,
            summary=summary
        ))

        print(f"\n  RAPPORT LLM")
        print(f"{'-'*70}")
        print(ctx.llm_response or "Aucune analyse disponible.")
        print(f"\n  Etapes de raisonnement ({len(ctx.reasoning_steps)}) :")
        for i, step in enumerate(ctx.reasoning_steps, 1):
            print(f"    {i}. {step}")
        if ctx.errors:
            print(f"\n  Erreurs ({len(ctx.errors)}) :")
            for e in ctx.errors:
                print(f"    - {e}")
        print(f"{'='*70}\n")

        return ctx

    def _check_ip_reputation(self, ctx: AgentContext, ip: str):
        result = check_abuseipdb(ip)
        ctx.tool_results["abuseipdb"] = result
        if not result["success"]:
            ctx.log_error(result["error"])

    def _llm_analysis(self, ctx: AgentContext, mcp_context: str = ""):
        threat_data = {
            "indicator_type": ctx.indicator_type,
            "indicator_value": ctx.indicator_value,
            "abuseipdb": ctx.tool_results.get("abuseipdb", {}),
            "dns_resolution": ctx.tool_results.get("dns_resolution", {}),
        }

        abuse = threat_data["abuseipdb"]
        score = abuse.get("abuse_score", 0) if abuse.get("success") else 0

        user_prompt = f"""Analyse ces donnees de Threat Intelligence :

Score de risque : {score}/100

IPs analysees :
{json.dumps([abuse] if abuse.get('success') else [], indent=2, ensure_ascii=False)}

Domaines analyses :
{json.dumps([], indent=2, ensure_ascii=False)}

IOCs detectes :
{json.dumps({("ips" if ctx.indicator_type == "ip" else "domains"): [ctx.indicator_value],
             "emails": []}, indent=2, ensure_ascii=False)}

{mcp_context}

Structure ta reponse en 3 parties :
1. **Resume** — synthese du niveau de risque global
2. **Analyse detaillee** — interpretation des indicateurs suspects
3. **Recommandations** — actions concretes a prendre
"""

        ctx.llm_response = groq_chat([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ])


def main():
    agent = ThreatIntelAgent()

    print("\n" + "=" * 70)
    print("  AGENT IA DE THREAT INTELLIGENCE — Mode interactif (MCP + Memoire)")
    print("  Exemples :")
    print("    - 'Verifie 185.220.101.45'")
    print("    - 'Quel est le score de google.com ?'")
    print("    - 'Peux-tu rappeler l'analyse precedente ?'")
    print("  Commandes :")
    print("    'exit'   -> quitter")
    print("    'memory' -> afficher l'historique")
    print("    'clear'  -> effacer la memoire")
    print("=" * 70)

    while True:
        try:
            query = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nFin de session.")
            break

        if query.lower() in ("exit", "quit", "q"):
            print("Fin de session.")
            break
        if not query:
            continue
        if query.lower() == "memory":
            if not agent.memory:
                print("  Aucune interaction en memoire.")
            else:
                print(f"\n  Historique ({len(agent.memory)} interactions) :")
                for i, entry in enumerate(agent.memory, 1):
                    s = f" [Score: {entry.score}/100]" if entry.score is not None else ""
                    print(f"  {i}. [{entry.timestamp[:19]}] \"{entry.query}\" -> {entry.indicator_type}:{entry.indicator_value}{s}")
            continue
        if query.lower() == "clear":
            agent.memory.clear()
            print("  Memoire effacee.")
            continue

        ctx = agent.run(query)


if __name__ == "__main__":
    main()
