// ticketing.js - Version optimisée
document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ Support simplifié chargé');
    
    // Vérifier si l'utilisateur est connecté
    const userJson = sessionStorage.getItem('user');
    const isLoggedIn = !!userJson;
    
    // Éléments DOM
    const newTicketCard = document.getElementById('newTicketCard');
    const createTicketBtn = document.getElementById('createTicketBtn');
    const newTicketModal = document.getElementById('newTicketModal');
    
    // Initialisation du modal
    const modalInstance = newTicketModal ? new bootstrap.Modal(newTicketModal) : null;

    // Base de connaissances
    const knowledgeBase = {
        vpn: { 
            title: 'Configuration VPN', 
            content: `Guide complet pour configurer votre VPN sécurisé :
            
1. Téléchargez le client VPN depuis votre espace client
2. Installez l'application sur votre appareil
3. Utilisez les identifiants fournis par email
4. Sélectionnez un serveur et connectez-vous

En cas de problème, contactez notre support.` 
        },
        antivirus: { 
            title: 'Mise à jour antivirus', 
            content: `Comment résoudre les problèmes de mise à jour :

1. Vérifiez votre connexion internet
2. Assurez-vous d'avoir assez d'espace disque
3. Redémarrez l'application antivirus
4. Téléchargez la dernière version depuis notre site

Si le problème persiste, ouvrez un ticket.` 
        },
        '2fa': { 
            title: 'Authentification à deux facteurs', 
            content: `Activez et configurez la 2FA pour plus de sécurité :

1. Dans votre espace client, allez dans Paramètres
2. Cliquez sur "Activer la 2FA"
3. Scannez le QR code avec Google Authenticator
4. Saisissez le code de vérification

La 2FA est maintenant active !` 
        },
        backup: { 
            title: 'Sauvegarde des données', 
            content: `Meilleures pratiques pour sauvegarder vos données :

- Effectuez des sauvegardes quotidiennes
- Utilisez la règle 3-2-1 : 3 copies, 2 supports, 1 hors-site
- Testez vos restaurations régulièrement
- Chiffrez vos sauvegardes sensibles

Contactez-nous pour une solution de backup automatisée.` 
        },
        phishing: { 
            title: 'Prévention phishing', 
            content: `Comment reconnaître et éviter les tentatives de phishing :

🔴 Signes d'alerte :
- Urgence dans le message
- Fautes d'orthographe
- Liens suspects
- Demandes d'informations personnelles

✅ Bonnes pratiques :
- Vérifiez toujours l'expéditeur
- Ne cliquez pas sur les liens suspects
- Utilisez l'authentification 2FA
- Signalez les emails frauduleux` 
        },
        network: { 
            title: 'Problèmes réseau', 
            content: `Diagnostic et résolution des problèmes de connectivité :

1. Redémarrez votre routeur/modem
2. Vérifiez les câbles réseau
3. Testez avec un autre appareil
4. Vérifiez votre configuration IP
5. Contactez votre FAI si nécessaire

Pour une assistance avancée, ouvrez un ticket.` 
        }
    };

    // Création d'un ticket
    const createTicket = () => {
        if (!isLoggedIn) {
            if (confirm('Vous devez être connecté pour créer un ticket. Voulez-vous vous connecter ?')) {
                window.location.href = 'auth.html';
            }
            return;
        }
        
        const subject = document.getElementById('ticketSubject')?.value;
        const category = document.getElementById('ticketCategory')?.value;
        const priority = document.getElementById('ticketPriority')?.value;
        const description = document.getElementById('ticketDescription')?.value;
        
        if (!subject || !category || !description) {
            alert('Veuillez remplir tous les champs obligatoires');
            return;
        }
        
        // Générer un ID unique
        const ticketId = '#TKT-' + Math.floor(Math.random() * 9000 + 1000);
        const user = JSON.parse(userJson);
        
        const newTicket = {
            id: ticketId,
            subject: subject,
            category: category,
            description: description,
            priority: priority || 'moyenne',
            status: 'ouvert',
            date: new Date().toLocaleDateString('fr-FR'),
            createdBy: user.email,
            createdByName: user.name
        };
        
        // Sauvegarder dans AppData
        if (window.AppData) {
            if (!AppData.tickets) AppData.tickets = [];
            AppData.tickets.push(newTicket);
        }
        
        alert(`✅ Ticket ${ticketId} créé avec succès ! Notre équipe vous répondra sous 24h.`);
        
        // Réinitialisation et fermeture
        document.getElementById('newTicketForm')?.reset();
        modalInstance?.hide();
    };

    // Consultation d'un article
    const viewArticle = (articleId) => {
        const article = knowledgeBase[articleId];
        if (article) {
            alert(`${article.title}\n\n${article.content}`);
        }
    };

    // Event listeners
    if (newTicketCard) {
        newTicketCard.addEventListener('click', () => {
            if (!isLoggedIn) {
                if (confirm('Vous devez être connecté pour créer un ticket. Voulez-vous vous connecter ?')) {
                    window.location.href = 'auth.html';
                }
                return;
            }
            modalInstance?.show();
        });
    }
    
    if (createTicketBtn) {
        createTicketBtn.addEventListener('click', createTicket);
    }

    // Articles de la base de connaissances
    document.querySelectorAll('.kb-article').forEach(article => {
        article.addEventListener('click', () => {
            const articleId = article.dataset.article;
            viewArticle(articleId);
        });
    });

    // Auto-fermeture du modal avec Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modalInstance) {
            modalInstance.hide();
        }
    });
});