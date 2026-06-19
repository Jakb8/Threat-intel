// ============================================
// access-control.js - Contrôle d'accès CORRIGÉ
// ============================================

// Vérifier l'accès à chaque page
function checkAccess() {
    const userJson = sessionStorage.getItem('user');
    const page = window.location.pathname.split('/').pop();
    
    // Pages publiques (accessibles sans connexion)
    const publicPages = ['index.html', 'auth.html', 'ticketing.html'];
    
    // Si la page est publique, on laisse passer
    if (publicPages.includes(page)) {
        return true;
    }
    
    // Pour les pages protégées (dashboard.html)
    if (!userJson) {
        window.location.href = 'auth.html';
        return false;
    }
    
    const user = JSON.parse(userJson);
    if (window.AppData) AppData.currentUser = user;
    
    // Seul l'admin peut accéder au dashboard
    if (page === 'dashboard.html' && user.role !== 'admin') {
        alert('Accès restreint - Administrateur uniquement');
        window.location.href = 'ticketing.html';
        return false;
    }
    
    return true;
}

// Déconnexion
function logout() {
    sessionStorage.removeItem('user');
    if (window.AppData) AppData.currentUser = null;
    window.location.href = 'index.html';
}

// NE PAS vérifier automatiquement au chargement
// Cette partie est supprimée pour ne pas bloquer les pages publiques