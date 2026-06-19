// ============================================
// data.js - Données de l'application
// ============================================

// 3 COMPTES PAR DÉFAUT
const UTILISATEURS = [
    { id: 1, name: 'Admin User', email: 'admin@cyber.com', password: '1234', role: 'admin', phone: '+33 6 12 34 56 78' },
    { id: 2, name: 'Client User', email: 'client@cyber.com', password: '1234', role: 'client', phone: '+33 6 23 45 67 89' },
    { id: 3, name: 'Test User', email: 'test@cyber.com', password: '1234', role: 'testeur', phone: '+33 6 34 56 78 90' }
];

// Données pour le dashboard
const ASSETS = [
    { id: 1, name: 'Serveur Principal', type: 'Serveur', ip: '192.168.1.10', os: 'Ubuntu 22.04', status: 'actif', lastScan: '15/03/2026' },
    { id: 2, name: 'Firewall', type: 'Équipement réseau', ip: '192.168.1.1', os: 'FortiOS', status: 'actif', lastScan: '14/03/2026' },
    { id: 3, name: 'Poste Direction', type: 'Station de travail', ip: '192.168.1.50', os: 'Windows 11', status: 'inactif', lastScan: '13/03/2026' },
    { id: 4, name: 'Base de données', type: 'Base de données', ip: '192.168.1.20', os: 'Ubuntu 20.04', status: 'vulnérable', lastScan: '10/03/2026' }
];

const TICKETS = [
    { id: '#TKT-001', subject: "Problème d'accès VPN", priority: 'haute', status: 'ouvert', date: '15/03/2026', createdBy: 'client@cyber.com' },
    { id: '#TKT-002', subject: 'Mise à jour antivirus', priority: 'basse', status: 'résolu', date: '14/03/2026', createdBy: 'test@cyber.com' },
    { id: '#TKT-003', subject: 'Configuration pare-feu', priority: 'moyenne', status: 'en cours', date: '12/03/2026', createdBy: 'client@cyber.com' }
];

// Données globales
window.AppData = {
    users: UTILISATEURS,
    assets: ASSETS,
    tickets: TICKETS,
    currentUser: null,
    nextAssetId: 5,
    nextTicketId: 4
};

console.log('✅ data.js chargé - 3 comptes disponibles');
console.log('👑 Admin: admin@cyber.com / 1234');
console.log('👤 Client: client@cyber.com / 1234');
console.log('🧪 Testeur: test@cyber.com / 1234');