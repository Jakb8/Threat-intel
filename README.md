# Rapport de Projet — Module Threat Intelligence CyberShield

## 1. Introduction

Ce projet a ete realise dans le cadre du module IA Generative du programme TEK-up. L'equipe est composee de deux personnes : Jihed Rezgui et Yacoub Bechi. L'objectif principal est de developper une console de Threat Intelligence (renseignement de menaces) combinant un workflow d'agent IA avec un systeme de raisonnement structure et un pipeline de Recherche Augmentee par Generation (RAG).

La menace cyber est en constante evolution. Les analystes en securite doivent traiter un volume croissant d'indicateurs de compromission (IOC) tels que des adresses IP, des domaines, des emails ou des empreintes de fichiers. Ce projet repond a ce besoin en proposant une plateforme integree qui automatise l'analyse de reputation, la synthese en langage naturel via un LLM (Large Language Model), et la recherche semantique dans des rapports de cybersecurite.

Le systeme est nomme CyberShield. Il se compose de plusieurs modules interconnectes : une API Flask pour l'analyse IOC, un agent IA en ligne de commande avec orchestration MCP (Model Context Protocol), une interface web sombre pour la visualisation des resultats, un systeme d'authentification avec controle d'acces par roles (RBAC), un tableau de bord admin, un systeme de ticketing, et un pipeline RAG pour la recherche semantique dans des rapports de bug bounty.

## 2. Objectifs du Projet

Les objectifs fixes pour ce projet sont les suivants :

- Analyser des indicateurs de compromission (IOC) en temps reel, incluant les adresses IP, les noms de domaine et les adresses email.
- Combiner des APIs de reputation externe (AbuseIPDB, VirusTotal) avec un LLM (Groq, modele llama-3.3-70b-versatile) pour produire une synthese en langage naturel exploitable par un analyste.
- Integrer un workflow d'agent IA avec des outils specialises (detection d'IOC, resolution DNS, verification de reputation) et une orchestration guidee par le contexte (MCP).
- Implementer un pipeline RAG pour la recherche semantique dans des rapports de cybersecurite (rapports HackerOne).
- Offrir une interface web professionnelle avec un design sombre, un score de risque visuel et un indicateur d'etat API.
- Mettre en place un systeme d'authentification avec trois niveaux de privileges (administrateur, client, testeur).
- Creer un tableau de bord admin pour la gestion des actifs et des tickets de support.
- Respecter les bonnes pratiques de securite : gestion des cles API, CORS, controle d'acces.

## 3. Description du Systeme

Le systeme CyberShield est une plateforme de Threat Intelligence modulaire. Chaque composant remplit une fonction specifique et communique avec les autres via des interfaces bien definies.

### Console Web IOC

La console web est le point d'entree principal pour l'analyste. Elle permet de coller un texte brut contenant des indicateurs de compromission. Le backend extrait automatiquement les IP, les domaines et les emails via des expressions regulieres, interroge les APIs de reputation, calcule un score de risque global (0-100), et produit une analyse synthetique via le LLM Groq.

L'interface utilisateur affiche :
- Un anneau de score colore (vert pour risque faible, jaune pour risque moyen, rouge pour risque eleve).
- Le nombre d'IPs, domaines et emails extraits.
- Les donnees brutes de reputation au format JSON.
- Une carte d'analyse LLM avec trois sections : Resume, Analyse detaillee, Recommandations.

### Agent CLI

L'agent CLI (ThreatIntelAgent) implemente un workflow structure d'intelligence artificielle. Il recoit une requete utilisateur, detecte automatiquement le type d'indicateur (IP, domaine, hash MD5, hash SHA256), applique les outils correspondants (resolution DNS, verification AbuseIPDB), et produit un rapport final via le LLM.

L'agent fonctionne en mode interactif (boucle REPL) et conserve un historique conversationnel. Il suit le protocole MCP (Model Context Protocol) avec un contexte formel, des etapes de raisonnement, et des decisions basees sur les resultats des outils.

### API Flask /analyze

L'API REST expose la fonctionnalite d'analyse via un point d'acces POST /analyze. Elle recoit un champ text, extrait les IOC, interroge AbuseIPDB et VirusTotal, calcule le score et retourne une reponse JSON structuree incluant l'analyse LLM.

### Dashboard Admin avec RBAC

Le tableau de bord admin permet la gestion des actifs informatiques (serveurs, stations de travail, equipements reseau) et des tickets de support. Il implemente un controle d'acces par roles avec trois niveaux :
- Administrateur : acces complet au CRUD des actifs, gestion des tickets, assignation.
- Client : consultation et creation de tickets.
- Testeur : acces limite, creation de tickets.

### Module Agent avec MCP et Memoire Conversationnelle

L'agent IA suit une architecture MCP (Model Context Protocol). Il maintient un AgentContext qui encapsule la requete utilisateur, l'horodatage, le type et la valeur de l'indicateur, les etapes de raisonnement, les resultats des outils, les erreurs, et la reponse LLM finale.

Chaque etape est loggee avec un horodatage. Les erreurs sont capturees et rapportees. L'orchestration est sequentielle : detection, verification DNS (si domaine), verification AbuseIPDB (si IP ou domaine resolu), puis analyse LLM.

### Module RAG

Le module RAG (non implemente dans le code final mais concu dans l'architecture) permettra de charger des documents PDF depuis le repertoire hackerone/, d'extraire le texte via mutool ou pdftotext, de decouper en chunks avec taille configurable et overlap, de generer des embeddings (TF-IDF vectoriel avec numpy ou via API), d'indexer avec FAISS pour la recherche par similarite cosinus, et de generer des reponses contextuelles via le LLM.

## 4. Architecture

L'architecture technique du systeme est organisee en plusieurs couches :

```
+------------------------------------------------------------------+
|                        FRONTEND WEB                              |
|  index.html  |  threatintel.html  |  auth.html  |  dashboard.html |
|  ticketing.html  |  CSS (Bootstrap 5)  |  JS (vanilla)           |
+------------------------------------------------------------------+
         |                        |                        |
         v                        v                        v
+------------------+  +---------------------+  +-------------------+
|  API Flask /     |  |  Agent IA CLI       |  |  Auth RBAC        |
|  analyze         |  |  (agent.py)         |  |  (sessionStorage) |
|  (app.py)        |  |  MCP Context        |  |  data.js          |
|  IOC extraction  |  |  Tools orchestration|  |  access-control.js|
|  Scoring         |  |  Memoire            |  +-------------------+
+------------------+  +---------------------+
         |                        |
         v                        v
+------------------+  +---------------------+
|  APIs Externes   |  |  LLM Groq           |
|  AbuseIPDB       |  |  llama-3.3-70b      |
|  VirusTotal      |  |  versatile          |
+------------------+  +---------------------+
         |
         v
+------------------+
|  Pipeline RAG    |
|  (conception)    |
|  FAISS +         |
|  Embeddings      |
+------------------+
```

### Schema ASCII de l'architecture

```
                           +-----------------------+
                           |    Navigateur Web     |
                           |  (Bootstrap 5, JS)    |
                           +----------+------------+
                                      |
                           HTTP POST /analyze
                                      |
                           +----------v------------+
                           |   Flask Backend       |
                           |   app.py:5000         |
                           +---+--------+--------+-+
                               |        |        |
                    +----------+  +-----+  +----+----------+
                    | AbuseIPDB |  | VT   |  | Groq LLM    |
                    | API v2    |  | API  |  | llama-3.3   |
                    +----------+  +-----+  +-------------+
                    
                           +-----------------------+
                           |  Agent IA CLI         |
                           |  ThreatIntelAgent     |
                           |  (agent.py)           |
                           +-----------------------+
                           |  MCP Context          |
                           |  -> detect_indicator  |
                           |  -> resolve_domain    |
                           |  -> check_abuseipdb   |
                           |  -> analyze_threats   |
                           +-----------------------+
```

### Stack technique

- Frontend : HTML5, CSS3, JavaScript vanilla, Bootstrap 5.3.2, Bootstrap Icons.
- Backend : Python 3, Flask, Flask-CORS.
- APIs externes : AbuseIPDB API v2, VirusTotal API v3, Groq API (llama-3.3-70b-versatile).
- Base vectorielle : FAISS (via numpy, prevue pour le module RAG).
- Stockage : fichiers JSON pour les embeddings et les donnees utilisateurs (sessionStorage cote client).
- Securite : CORS configure, controle d'acces cote client avec sessionStorage, hashage des mots de passe (prevue).

## 5. Implementation Detaillee

### 5.1 Application Web (app.py + threatintel.html)

#### Backend Flask (app.py)

Le fichier app.py implemente un serveur Flask exposant une API REST. La route principale est POST /analyze qui accepte un JSON avec un champ text.

La fonction extract_iocs utilise trois expressions regulieres pour extraire les indicateurs :
- IP_REGEX : r'\b(?:\d{1,3}\.){3}\d{1,3}\b' pour les adresses IPv4.
- EMAIL_REGEX : r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' pour les emails.
- DOMAIN_REGEX : r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b' pour les noms de domaine.

La fonction check_ip_abuse interroge l'API AbuseIPDB avec une cle API et recupere le score de confiance d'abus, le pays, le FAI, et l'historique de signalement.

La fonction check_domain interroge l'API VirusTotal pour la reputation des domaines.

La fonction calculate_score agrege les scores de confiance d'abus de toutes les IPs analysees et retourne un score plafonne a 100.

La fonction analyze_iocs orchestre l'ensemble : elle appelle les verifications pour chaque IP et domaine, construit un dictionnaire threat_data, et appelle analyze_threats du module groq pour la synthese LLM.

#### Frontend (threatintel.html)

L'interface est concue dans un theme sombre (gradient de #0a0e14 a #1a1f2e). Elle comprend :

- Une barre de navigation fluide avec Bootstrap.
- Un hero section presentant le service Threat Intelligence.
- Un indicateur d'etat API en ligne/ hors ligne avec un point colore.
- Une carte console avec un textarea pour saisir le texte a analyser.
- Un bouton "Analyser" avec animation de chargement.
- Une carte de resultats avec l'anneau de score colore (score-low: vert, score-mid: jaune, score-high: rouge).
- Un affichage du nombre d'IPs, domaines et emails extraits.
- Une section donnees brutes au format JSON.
- Une carte d'analyse LLM avec rendu HTML du texte genere.

Le JavaScript cote client utilise fetch pour appeler l'API, parse la reponse JSON, met a jour le DOM avec les resultats, et affiche des notifications toast.

### 5.2 Agent IA (agent.py)

L'agent IA est implemente dans agent.py avec une architecture orientee objet.

#### Classe AgentContext

La classe AgentContext (dataclass Python) encapsule l'etat complet de l'analyse :
- user_query : la requete originale de l'utilisateur.
- timestamp : l'horodatage de l'analyse.
- indicator_type et indicator_value : le type et la valeur de l'IOC detecte.
- reasoning_steps : la liste des etapes de raisonnement.
- tool_results : un dictionnaire contenant les resultats de chaque outil.
- errors : la liste des erreurs rencontrees.
- llm_response : la reponse generee par le LLM.

Les methodes log_step et log_error permettent de tracer l'execution.

#### Detection d'IOC

La fonction detect_indicator analyse le texte de la requete et detecte le type d'indicateur avec une priorite definie :
1. SHA256 (64 caracteres hexadecimaux)
2. MD5 (32 caracteres hexadecimaux)
3. Adresse IP (4 octets, validation 0-255)
4. Nom de domaine

Cette hierarchie permet de traiter correctement les collisions potentielles (par exemple, une chaine hexadecimale de 32 caracteres pourrait ressembler a une adresse IP valide).

#### Resolution DNS

La fonction resolve_domain utilise socket.gethostbyname pour resoudre un nom de domaine en adresse IP. Elle retourne un dictionnaire avec succes ou echec et un message d'erreur.

#### Verification AbuseIPDB

La fonction check_abuseipdb interroge l'API AbuseIPDB avec gestion des erreurs :
- Timeout : message clair.
- Erreur de connexion : message explicite.
- Code 401 : cle API invalide.
- Code 429 : quota depasse.
- Autres erreurs : capture generale.

Elle retourne un dictionnaire structure avec l'IP, le score d'abus, le pays, le FAI, le nombre de signalements, le statut whitelist, et la date du dernier signalement.

#### Classe ThreatIntelAgent

La classe ThreatIntelAgent orchestre le workflow :

1. Analyse de la requete utilisateur pour detecter un indicateur.
2. Si aucun indicateur : arret avec message d'erreur.
3. Si IP : appel direct a AbuseIPDB.
4. Si domaine : resolution DNS d'abord, puis AbuseIPDB sur l'IP resolue.
5. Si hash : note (hors perimetre AbuseIPDB).
6. Analyse LLM finale via Groq.

Chaque etape est loggee dans le raisonnement. Les resultats des outils sont stockes dans le contexte.

#### Mode Interactif

La fonction main lance l'agent en mode interactif (REPL). L'utilisateur peut saisir des requetes en continu. La session se termine par la commande exit.

### 5.3 Pipeline RAG (conception)

Le pipeline RAG est prevu dans l'architecture mais n'a pas ete implemente dans la version finale du code. La conception comprend :

- Chargement de documents PDF depuis le repertoire hackerone/ (rapports de bug bounty pour Alsco, Banco Plata, Unico IDTech, Vodafone Oman).
- Extraction de texte via mutool ou pdftotext.
- Decoupage en chunks avec taille configurable et overlap.
- Generation d'embeddings TF-IDF avec numpy (ou via API d'embedding).
- Indexation FAISS avec similarite cosinus.
- Retrieval des chunks les plus pertinents pour une requete.
- Generation de reponse LLM avec contexte augmente.

Cette fonctionnalite permettra de rechercher semantiquement dans les rapports de securite pour trouver des vulnerabilites similaires, des techniques d'attaque ou des recommandations.

### 5.4 Authentification et RBAC

L'authentification est implementee cote client avec sessionStorage.

#### Systeme de Roles (data.js)

Trois utilisateurs par defaut sont preconfigures :
- Administrateur : admin@cyber.com (role: admin)
- Client : client@cyber.com (role: client)
- Testeur : test@cyber.com (role: testeur)

Chaque utilisateur possede un identifiant, un nom, un email, un mot de passe, un role et un telephone.

#### Controle d'Acces (access-control.js)

La fonction checkAccess verifie :
- Si la page est publique (index.html, auth.html, ticketing.html) : acces autorise.
- Si la page est protegee (dashboard.html) : verifie la presence d'un utilisateur connecte dans sessionStorage.
- Si l'utilisateur n'est pas admin : redirection vers ticketing.html avec un message d'alerte.

#### Formulaire d'Authentification (auth.js + auth.html)

Le module d'authentification propose :
- Un onglet de connexion avec email et mot de passe.
- Un onglet d'inscription avec validation de mot de passe (force), confirmation, et acceptation des conditions.
- Un indicateur visuel de force de mot de passe (faible, moyen, fort) base sur des criteres : minuscule, majuscule, chiffre, caractere special, longueur >= 8.
- La verification que l'email n'est pas deja utilise.
- La redirection vers le dashboard (admin) ou ticketing (client/testeur) apres connexion.

### 5.5 Dashboard Admin (dashboard.html + dashboard.js)

Le tableau de bord admin offre :

- Une barre laterale avec navigation : Vue d'ensemble, Mes actifs, Tickets support, Rapports, Parametres, Deconnexion.
- Une carte de bienvenue personnalisee avec le prenom de l'utilisateur.
- Des statistiques : actifs proteges, tickets resolus, alertes critiques, temps de reponse.
- La gestion des actifs avec un tableau complet : ID, nom, type, adresse IP, systeme d'exploitation, statut, actions (editer, supprimer, scanner).
- La gestion des tickets avec selection de priorite et statut, assignation a un utilisateur.
- Un modal d'ajout/edition d'actif avec validation d'adresse IP.
- Un modal de confirmation de suppression.
- Un modal d'assignation de ticket.
- La simulation de scan avec changement de statut aleatoire (30% de chance de devenir vulnerable).

### 5.6 Systeme de Ticketing (ticketing.html + ticketing.js)

Le systeme de support propose :
- Une carte pour creer un nouveau ticket (modal avec sujet, categorie, priorite, description, pieces jointes).
- Une base de connaissances avec six articles : Configuration VPN, Mise a jour antivirus, Authentification 2FA, Sauvegarde, Prevention phishing, Problemes reseau.
- Chaque article s'ouvre dans un modal avec un contenu guide.
- La creation de ticket genere un identifiant unique (#TKT-XXXX) et l'ajoute aux donnees globales.

## 6. Resultats et Tests

### Tests avec IPs Reelles

L'IP 185.220.101.45 a ete testee. Cette IP est hebergee chez Hetzner (Allemagne). Le score de confiance d'abus retourne par AbuseIPDB etait de 75/100, ce qui correspond a un risque eleve. L'analyse LLM a correctement identifie le niveau de risque et formule des recommandations.

### Tests avec Domaines Malveillants

Des domaines suspects ont ete soumis a l'analyse. La resolution DNS a fonctionne correctement, et les domaines ont ete resolves en adresses IP avant verification AbuseIPDB. Les domaines legitimes (google.com) ont obtneu des scores faibles.

### Tests du RAG

Les rapports HackerOne stocks dans le repertoire hackerone/ contiennent des donnees de bug bounty reelles pour quatre programmes :
- Alsco : vulnerabilites web (SSL/TLS, acces direct IP, sous-domaines cPanel exposes).
- Banco Plata : exposition de fichier .env.json.
- Unico IDTech : fuites OIDC, exposition GCP, cookie session statique.
- Vodafone Oman : decouverte de chemins serveur, SSRF Yoast, contournement WAF, enumeration d'auteurs.

Ces rapports sont disponibles au format markdown et PDF pour une future integration RAG.

### Tests de l'Agent en Mode Interactif

L'agent a ete teste avec des requetes comme :
- "Cette IP 185.220.101.45 est-elle suspecte ?" : detection correcte de l'IP, verification AbuseIPDB, rapport LLM.
- "Verifie la reputation de google.com" : resolution DNS, verification AbuseIPDB, rapport LLM.
- "Analyse ce hash md5 d41d8cd98f00b204e9800998ecf8427e" : detection du hash, note hors perimetre, analyse LLM.
- Requete sans IOC : message d'erreur clair.

## 7. Lien avec les Concepts du Cours

Ce projet met en pratique les concepts suivants du module IA Generative :

### Workflow d'Agent

- Tools : les fonctions detect_indicator, resolve_domain, check_abuseipdb, et analyze_threats sont les outils mis a disposition de l'agent.
- Orchestration : la methode run de ThreatIntelAgent orchestre le flux en fonction du type d'indicateur detecte.
- MCP (Model Context Protocol) : la classe AgentContext implemente le contexte formel avec timestamp, etapes de raisonnement, resultats d'outils, et etat global.
- Memoire conversationnelle : l'agent conserve un historique des requetes et reponses pendant la session interactive.
- Decisions : l'agent choisit dynamiquement la sequence d'outils en fonction du type d'IOC (resolution DNS uniquement pour les domaines, AbuseIPDB pour les IP).

### RAG (Retrieval Augmented Generation)

La conception du module RAG couvre :
- Chunking : decoupage de documents en segments de taille optimale avec overlap.
- Embeddings : transformation des chunks en vecteurs numeriques (TF-IDF ou API).
- Vector Store : indexation des embeddings dans FAISS pour la recherche par similarite cosinus.
- Retrieval : selection des chunks les plus pertinents pour une requete.
- Generation : injection du contexte dans le prompt LLM pour une reponse informee.

### LLM (Large Language Model)

- Prompt Engineering : le system prompt definit le role (analyste cybersecurite), la structure de sortie (Resume, Analyse detaillee, Recommandations), et le ton (concis, technique, precis).
- Groq API : utilisation de l'API Groq avec le modele llama-3.3-70b-versatile pour la generation en langage naturel.
- Structured Output : le prompt impose un format sans JSON, en texte structure avec des sections markdown.

### Securite

- Gestion des cles API : les cles AbuseIPDB et VirusTotal sont stockees dans le code (limite identifiee, amelioration prevue avec variables d'environnement).
- CORS : configure avec Flask-CORS (actuellement ouvert a toutes les origines, a restreindre en production).
- RBAC : controle d'acces par roles implemente cote client avec redirection conditionnelle.

## 8. Limites et Ameliorations Futures

### Limites Identifiees

1. **Cles API en dur** : les cles AbuseIPDB, VirusTotal et Groq sont directement dans le code source (app.py, agent.py, groq.py). Cela represente un risque de securite. Solution : utiliser des variables d'environnement ou un fichier .env.

2. **CORS ouvert** : la configuration CORS autorise toutes les origines (*). En production, il faudrait restreindre aux domaines autorises.

3. **Scalabilite de FAISS** : pour de gros volumes de documents, FAISS en memoire peut devenir limite. Solution : utiliser une base vectorielle persistante (ChromaDB, Pinecone) ou un index FAISS sur disque.

4. **Interface RAG dans le frontend** : le pipeline RAG est en conception et n'a pas d'interface utilisateur. Un onglet "Recherche semantique" dans le dashboard permettrait d'interroger les rapports.

5. **Support de plus de formats de documents** : actuellement, seuls les PDF et markdown sont prevus. L'ajout du support DOCX, HTML, et TXT elargirait la base de connaissances.

6. **Authentification cote serveur** : l'authentification est entierement cote client avec sessionStorage. Une API d'authentification avec JWT serait plus securisee.

7. **Tests unitaires** : aucun test unitaire n'est implemente. L'ajout de tests avec pytest pour les fonctions d'extraction IOC, de scoring, et les outils de l'agent ameliorerait la robustesse.

### Ameliorations Futures

1. **Module RAG complet** : implementer le pipeline complet avec chargement PDF, chunking, embeddings, indexation FAISS, retrieval et generation.

2. **Interface de chat agent** : ajouter une interface web pour l'agent interactif avec historique conversationnel.

3. **Notifications en temps reel** : utiliser WebSocket pour les notifications de scan et de tickets.

4. **Export de rapports** : generer des rapports PDF ou CSV a partir des analyses.

5. **Integration Shodan/Censys** : ajouter des sources de renseignement supplementaires pour la reconnaissance.

6. **Base de donnees persistante** : remplacer les fichiers JSON par SQLite ou PostgreSQL.

7. **Deploiement Docker** : containeriser l'application avec Docker Compose (Flask + Nginx).

8. **CI/CD** : mettre en place une pipeline d'integration et de deploiement continus.

## 9. Conclusion

Ce projet de Threat Intelligence a permis de developper une plateforme fonctionnelle combinant un agent IA avec orchestration MCP, une API REST pour l'analyse d'IOC, une interface web professionnelle, et un systeme de gestion avec RBAC.

Les competences demontrees incluent :
- La conception et l'implementation d'un workflow d'agent IA avec outils, contexte et memoire.
- L'integration d'APIs externes (AbuseIPDB, VirusTotal, Groq).
- Le prompt engineering pour la generation structuree en langage naturel.
- La programmation web full-stack avec Flask, Bootstrap 5 et JavaScript vanilla.
- La mise en place d'un systeme d'authentification et de controle d'acces.
- L'architecture d'un pipeline RAG avec vector store et embeddings.

Le projet constitue une base solide pour une solution de Threat Intelligence professionalisable, avec des pistes d'amelioration claires identifiees pour la securite, la scalabilite et les fonctionnalites.

