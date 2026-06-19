document.addEventListener('DOMContentLoaded', () => {
    const userJson = sessionStorage.getItem('user');
    const isLoggedIn = !!userJson;

    const newTicketCard = document.getElementById('newTicketCard');
    const createTicketBtn = document.getElementById('createTicketBtn');
    const newTicketModal = document.getElementById('newTicketModal');
    const modalInstance = newTicketModal ? new bootstrap.Modal(newTicketModal) : null;

    const knowledgeBase = {
        vpn: {
            title: 'Configuration VPN',
            content: `<h6>Guide complet pour configurer votre VPN sécurisé :</h6>
<ol class="mb-0">
<li>Téléchargez le client VPN depuis votre espace client</li>
<li>Installez l'application sur votre appareil</li>
<li>Utilisez les identifiants fournis par email</li>
<li>Sélectionnez un serveur et connectez-vous</li>
</ol>
<p class="mt-3 mb-0 text-muted">En cas de problème, contactez notre support.</p>`
        },
        antivirus: {
            title: 'Mise à jour antivirus',
            content: `<h6>Comment résoudre les problèmes de mise à jour :</h6>
<ol class="mb-0">
<li>Vérifiez votre connexion internet</li>
<li>Assurez-vous d'avoir assez d'espace disque</li>
<li>Redémarrez l'application antivirus</li>
<li>Téléchargez la dernière version depuis notre site</li>
</ol>
<p class="mt-3 mb-0 text-muted">Si le problème persiste, ouvrez un ticket.</p>`
        },
        '2fa': {
            title: 'Authentification à deux facteurs',
            content: `<h6>Activez et configurez la 2FA pour plus de sécurité :</h6>
<ol class="mb-0">
<li>Dans votre espace client, allez dans Paramètres</li>
<li>Cliquez sur "Activer la 2FA"</li>
<li>Scannez le QR code avec Google Authenticator</li>
<li>Saisissez le code de vérification</li>
</ol>
<p class="mt-3 mb-0 text-success fw-bold">La 2FA est maintenant active !</p>`
        },
        backup: {
            title: 'Sauvegarde des données',
            content: `<h6>Meilleures pratiques pour sauvegarder vos données :</h6>
<ul class="mb-0">
<li>Effectuez des sauvegardes quotidiennes</li>
<li>Utilisez la règle 3-2-1 : 3 copies, 2 supports, 1 hors-site</li>
<li>Testez vos restaurations régulièrement</li>
<li>Chiffrez vos sauvegardes sensibles</li>
</ul>
<p class="mt-3 mb-0 text-muted">Contactez-nous pour une solution de backup automatisée.</p>`
        },
        phishing: {
            title: 'Prévention phishing',
            content: `<h6>Comment reconnaître et éviter les tentatives de phishing :</h6>
<div class="alert alert-danger">
<strong>🔴 Signes d'alerte :</strong>
<ul class="mb-0">
<li>Urgence dans le message</li>
<li>Fautes d'orthographe</li>
<li>Liens suspects</li>
<li>Demandes d'informations personnelles</li>
</ul>
</div>
<div class="alert alert-success">
<strong>✅ Bonnes pratiques :</strong>
<ul class="mb-0">
<li>Vérifiez toujours l'expéditeur</li>
<li>Ne cliquez pas sur les liens suspects</li>
<li>Utilisez l'authentification 2FA</li>
<li>Signalez les emails frauduleux</li>
</ul>
</div>`
        },
        network: {
            title: 'Problèmes réseau',
            content: `<h6>Diagnostic et résolution des problèmes de connectivité :</h6>
<ol class="mb-0">
<li>Redémarrez votre routeur/modem</li>
<li>Vérifiez les câbles réseau</li>
<li>Testez avec un autre appareil</li>
<li>Vérifiez votre configuration IP</li>
<li>Contactez votre FAI si nécessaire</li>
</ol>
<p class="mt-3 mb-0 text-muted">Pour une assistance avancée, ouvrez un ticket.</p>`
        }
    };

    const showArticle = (articleId) => {
        const article = knowledgeBase[articleId];
        if (!article) return;
        document.getElementById('kbModalTitle').textContent = article.title;
        document.getElementById('kbModalBody').innerHTML = article.content;
        const kbModal = new bootstrap.Modal(document.getElementById('kbModal'));
        kbModal.show();
    };

    const createTicket = () => {
        if (!isLoggedIn) {
            showToast('Vous devez être connecté pour créer un ticket', 'warning');
            setTimeout(() => window.location.href = 'auth.html', 1500);
            return;
        }

        const subject = document.getElementById('ticketSubject')?.value;
        const category = document.getElementById('ticketCategory')?.value;
        const priority = document.getElementById('ticketPriority')?.value;
        const description = document.getElementById('ticketDescription')?.value;

        if (!subject || !category || !description) {
            showToast('Veuillez remplir tous les champs obligatoires', 'warning');
            return;
        }

        const ticketId = '#TKT-' + Math.floor(Math.random() * 9000 + 1000);
        const user = JSON.parse(userJson);

        const newTicket = {
            id: ticketId,
            subject,
            category,
            description,
            priority: priority || 'moyenne',
            status: 'ouvert',
            date: new Date().toLocaleDateString('fr-FR'),
            createdBy: user.email,
            createdByName: user.name
        };

        if (window.AppData) {
            if (!AppData.tickets) AppData.tickets = [];
            AppData.tickets.push(newTicket);
        }

        showToast(`✅ Ticket ${ticketId} créé ! Notre équipe vous répondra sous 24h.`, 'success');

        document.getElementById('newTicketForm')?.reset();
        modalInstance?.hide();
    };

    if (newTicketCard) {
        newTicketCard.addEventListener('click', () => {
            if (!isLoggedIn) {
                showToast('Veuillez vous connecter pour créer un ticket', 'warning');
                setTimeout(() => window.location.href = 'auth.html', 1500);
                return;
            }
            modalInstance?.show();
        });
    }

    if (createTicketBtn) {
        createTicketBtn.addEventListener('click', createTicket);
    }

    document.querySelectorAll('.kb-article').forEach(article => {
        article.addEventListener('click', () => {
            const articleId = article.dataset.article;
            showArticle(articleId);
        });
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modalInstance) {
            modalInstance.hide();
        }
    });
});
