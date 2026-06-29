# CyberShield — Plateforme de Threat Intelligence

**TEK-up | Module IA Generative**  
Équipe : Jihed Rezgui & Yacoub Bechi

---

## Résumé

Plateforme modulaire de **renseignement de menaces** combinant :
- Agent IA avec orchestration MCP
- Pipeline RAG pour la recherche sémantique
- API REST d'analyse IOC
- Console web avec design sombre
- Dashboard admin avec RBAC
- Système de ticketing

---

## Problématique

Les analystes en sécurité doivent traiter un **volume croissant d'IOC** (IP, domaines, emails, hashs).

Problèmes :
- Analyse manuelle chronophage
- Multiplicité des sources de réputation (AbuseIPDB, VirusTotal)
- Difficulté de synthèse et de corrélation

**Notre solution** : automatiser l'analyse via un agent IA + LLM.

---

## Architecture

```
Navigateur Web (Bootstrap 5, JS)
        |
   POST /analyze
        |
  Flask Backend (app.py:5000)
    |         |         |
AbuseIPDB  VirusTotal  Groq LLM
    |                   (llama-3.3-70b)
    |
  Agent IA CLI (MCP Context)
    -> detect_indicator
    -> resolve_domain
    -> check_abuseipdb
    -> analyze_threats
```

---

## Fonctionnalités Clés

### 🎯 Console Web IOC
- Analyse temps réel d'IOC par Regex
- Score de risque visuel (0-100) avec anneau coloré
- Synthèse LLM : Résumé, Analyse, Recommandations
- Intégration AbuseIPDB + VirusTotal

### 🤖 Agent IA (CLI)
- Détection intelligente d'IOC (IP, domaine, MD5, SHA256)
- Résolution DNS puis vérification AbuseIPDB
- Contexte MCP avec étapes de raisonnement
- Mémoire conversationnelle (session REPL)

### 🔍 Pipeline RAG (conception)
- Indexation vectorielle FAISS
- Embeddings TF-IDF / API
- Recherche sémantique dans rapports HackerOne
- Génération augmentée par contexte

### 🔐 Authentification & RBAC
- 3 rôles : Administrateur, Client, Testeur
- Contrôle d'accès par page
- Indicateur de force de mot de passe

### 📊 Dashboard Admin
- Gestion CRUD des actifs (serveurs, stations, équipements)
- Simulation de scan avec détection de vulnérabilités
- Assignation de tickets
- Statistiques en temps réel

### 🎫 Système de Ticketing
- Création de tickets par catégorie/priorité
- Base de connaissances (6 articles)
- Identification unique (#TKT-XXXX)

---

## Stack Technique

| Composant | Technologie |
|-----------|-------------|
| Frontend | HTML5, CSS3, JS Vanilla, Bootstrap 5.3.2 |
| Backend | Python 3, Flask, Flask-CORS |
| APIs | AbuseIPDB v2, VirusTotal v3, Groq API |
| LLM | llama-3.3-70b-versatile (Groq) |
| Vector Store | FAISS + NumPy |
| Stockage | JSON, sessionStorage |

---

## Tests & Résultats

**IP malveillante** `185.220.101.45` (Hetzner, Allemagne) :
- Score AbuseIPDB : **75/100** — risque élevé
- LLM a correctement identifié et recommandé des actions

**Domaine légitime** `google.com` :
- Score faible, aucune alerte

**Agent CLI** :
- ✅ Détection IP → AbuseIPDB → Rapport LLM
- ✅ Détection domaine → DNS → AbuseIPDB → Rapport LLM
- ✅ Détection hash → Note hors périmètre → Rapport LLM
- ✅ Requête sans IOC → Message d'erreur clair

**Rapports HackerOne** (Alsco, Banco Plata, Unico IDTech, Vodafone Oman) :
- Prêts pour intégration RAG

---

## Concepts du Cours Appliqués

### Workflow d'Agent
- **Tools** : detect_indicator, resolve_domain, check_abuseipdb, analyze_threats
- **Orchestration** : séquence dynamique selon type d'IOC
- **MCP** : AgentContext avec timestamp, reasoning_steps, tool_results
- **Mémoire** : historique conversationnel en session REPL

### RAG
- Chunking → Embeddings → FAISS → Retrieval → Generation

### LLM
- Prompt Engineering (rôle analyste, format structuré)
- Groq API avec llama-3.3-70b-versatile
- Sortie structurée en sections markdown

### Sécurité
- Gestion API keys (limite : en dur → prévoir .env)
- CORS configuré
- RBAC côté client

---

## Limites Identifiées

1. 🔴 **Clés API en dur** dans le code source
2. 🔴 **CORS ouvert** (*) — à restreindre en production
3. 🔴 **Authentification côté client** — JWT côté serveur recommandé
4. 🟡 **Module RAG non finalisé** dans le frontend
5. 🟡 **Pas de tests unitaires** (pytest à ajouter)
6. 🟡 **Stockage fichier JSON** → SQLite/PostgreSQL

---

## Améliorations Futures

1. Module RAG complet avec interface utilisateur
2. Chat web pour l'agent IA interactif
3. WebSocket pour notifications temps réel
4. Export PDF/CSV des rapports
5. Intégration Shodan / Censys
6. Base de données persistante (SQLite/PostgreSQL)
7. Déploiement Docker (Flask + Nginx)
8. CI/CD pipeline

---

## Conclusion

✅ Plateforme fonctionnelle de Threat Intelligence  
✅ Agent IA avec orchestration MCP et mémoire  
✅ API REST pour analyse IOC temps réel  
✅ Interface web professionnelle (dark theme)  
✅ Dashboard RBAC + Ticketing  
✅ Architecture RAG conçue et prête à implémenter  

**Base solide pour une solution professionalisable** avec des pistes d'amélioration claires en sécurité, scalabilité et fonctionnalités.
