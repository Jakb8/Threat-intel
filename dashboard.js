// dashboard.js - Version corrigée
document.addEventListener('DOMContentLoaded', () => {
    const user = JSON.parse(sessionStorage.getItem('user') || 'null');
    if (!user || user.role !== 'admin') {
        alert(user ? 'Accès restreint' : 'Veuillez vous connecter');
        return window.location.href = user ? 'ticketing.html' : 'auth.html';
    }

    // Données
    let { assets = [], tickets = [] } = window.AppData || {};
    let nextId = window.AppData?.nextAssetId || 5;
    const modal = document.getElementById('assetModal') ? new bootstrap.Modal(document.getElementById('assetModal')) : null;

    // Éléments DOM
    const el = id => document.getElementById(id);
    const setHTML = (id, html) => el(id) && (el(id).innerHTML = html);
    const setText = (id, text) => el(id) && (el(id).textContent = text);

    // Initialisation
    setText('userNameDisplay', user.name);
    setText('userEmailDisplay', user.email);
    setText('welcomeName', user.name.split(' ')[0]);
    if (el('settingsName')) el('settingsName').value = user.name;
    if (el('settingsEmail')) el('settingsEmail').value = user.email;

    // Utilitaires
    const statusClass = s => ({ actif:'bg-success', inactif:'bg-secondary', vulnérable:'bg-danger', 'en scan':'bg-warning', maintenance:'bg-warning' }[s] || 'bg-secondary');
    const priorityColor = p => ({ basse:'#198754', moyenne:'#ffc107', haute:'#dc3545', critique:'#dc3545' }[p] || '#6c757d');
    const statusColor = s => ({ ouvert:'#ffc107', 'en cours':'#0dcaf0', résolu:'#198754', fermé:'#6c757d' }[s] || '#6c757d');
    const validateIP = ip => /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(ip);

    // Rendu tableaux
    const render = () => {
        // Tableau des actifs simplifié
        setHTML('assetsTableBody', assets.map(a => `<tr>
            <td>${a.id}</td>
            <td>${a.name}</td>
            <td>${a.type}</td>
            <td><span class="badge ${statusClass(a.status)}">${a.status}</span></td>
            <td>${a.lastScan || '-'}</td>
            <td>
                <button class="btn btn-sm btn-outline-warning" onclick="editAsset(${a.id})"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteAsset(${a.id})"><i class="bi bi-trash"></i></button>
                <button class="btn btn-sm btn-outline-info" onclick="scanAsset(${a.id})"><i class="bi bi-search"></i></button>
            </td>
        </tr>`).join('') || '<tr><td colspan="6" class="text-center">Aucun actif</td></tr>');

        // Tableau des actifs complet
        setHTML('assetsFullTableBody', assets.map(a => `<tr>
            <td>${a.id}</td>
            <td>${a.name}</td>
            <td>${a.type}</td>
            <td>${a.ip || '-'}</td>
            <td>${a.os || '-'}</td>
            <td><span class="badge ${statusClass(a.status)}">${a.status}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-warning" onclick="editAsset(${a.id})"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteAsset(${a.id})"><i class="bi bi-trash"></i></button>
                <button class="btn btn-sm btn-outline-info" onclick="scanAsset(${a.id})"><i class="bi bi-search"></i></button>
            </td>
        </tr>`).join('') || '<tr><td colspan="7" class="text-center">Aucun actif</td></tr>');

        // Tableau des tickets - CORRIGÉ !
        setHTML('ticketsTableBody', tickets.map(t => `<tr>
            <td>${t.id}</td>
            <td>${t.subject}</td>
            <td>
                <select class="form-select form-select-sm priority" data-id="${t.id}" style="background:${priorityColor(t.priority)};color:white;border:none;">
                    ${['basse', 'moyenne', 'haute', 'critique'].map(p => 
                        `<option value="${p}" ${t.priority === p ? 'selected' : ''}>${p}</option>`
                    ).join('')}
                </select>
            </td>
            <td>
                <select class="form-select form-select-sm status" data-id="${t.id}" style="background:${statusColor(t.status)};color:white;border:none;">
                    ${['ouvert', 'en cours', 'résolu', 'fermé'].map(s => 
                        `<option value="${s}" ${t.status === s ? 'selected' : ''}>${s}</option>`
                    ).join('')}
                </select>
            </td>
            <td>${t.date || '-'}</td>
            <td>
                <button class="btn btn-sm btn-warning" onclick="assignTicket('${t.id}')"><i class="bi bi-person-plus"></i></button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteTicket('${t.id}')"><i class="bi bi-trash"></i></button>
            </td>
        </tr>`).join('') || '<tr><td colspan="6" class="text-center">Aucun ticket</td></tr>');

        setText('assetCount', assets.length);

        // Event listeners pour les selects
        document.querySelectorAll('.priority').forEach(s => s.addEventListener('change', function() {
            const t = tickets.find(t => t.id == this.dataset.id);
            if(t) { 
                t.priority = this.value; 
                this.style.background = priorityColor(this.value); 
                if(window.AppData) AppData.tickets = tickets; 
            }
        }));
        
        document.querySelectorAll('.status').forEach(s => s.addEventListener('change', function() {
            const t = tickets.find(t => t.id == this.dataset.id);
            if(t) { 
                t.status = this.value; 
                this.style.background = statusColor(this.value); 
                if(window.AppData) AppData.tickets = tickets; 
            }
        }));
    };

    // Actions assets
    window.editAsset = (id) => {
        const a = assets.find(a => a.id === id);
        if(a) {
            el('assetId').value = a.id;
            el('assetName').value = a.name;
            el('assetType').value = a.type;
            el('assetIp').value = a.ip;
            el('assetOs').value = a.os || '';
            el('assetStatus').value = a.status;
            el('modalTitle').textContent = 'Modifier actif';
        } else {
            el('assetForm')?.reset();
            el('assetId').value = '';
            el('modalTitle').textContent = 'Ajouter actif';
        }
        modal?.show();
    };

    window.deleteAsset = (id) => { 
        if(confirm('Supprimer cet actif ?')) { 
            assets = assets.filter(a => a.id !== id); 
            if(window.AppData) AppData.assets = assets; 
            render(); 
        } 
    };

    window.scanAsset = (id) => {
        const a = assets.find(a => a.id === id);
        if(!a) return;
        const prev = a.status;
        a.status = 'en scan'; 
        render();
        alert(`Scan lancé pour ${a.name}`);
        setTimeout(() => {
            a.status = Math.random() < 0.3 ? 'vulnérable' : (prev === 'vulnérable' ? 'actif' : prev);
            a.lastScan = new Date().toLocaleDateString('fr-FR');
            render();
            alert(a.status === 'vulnérable' ? `⚠️ Vulnérabilités sur ${a.name}` : `✅ Scan terminé pour ${a.name}`);
        }, 2000);
    };

    // Actions tickets
    window.assignTicket = (id) => {
        const t = tickets.find(t => t.id == id);
        if(!t) return;
        const users = AppData?.users?.filter(u => u.role !== 'admin') || [];
        if(users.length === 0) return alert('Aucun utilisateur disponible');
        
        const email = prompt(`Assigner à :\n${users.map(u => `${u.name} (${u.email})`).join('\n')}\n\nEntrez l'email:`);
        if(email) {
            const u = users.find(u => u.email === email);
            if(u) {
                t.assignedTo = email;
                t.assignedToName = u.name;
                if(window.AppData) AppData.tickets = tickets;
                alert(`Ticket assigné à ${u.name}`);
            } else {
                alert('Utilisateur non trouvé');
            }
        }
    };

    window.deleteTicket = (id) => { 
        if(confirm('Supprimer ce ticket ?')) { 
            tickets = tickets.filter(t => t.id != id); 
            if(window.AppData) AppData.tickets = tickets; 
            render(); 
        } 
    };

    // Sauvegarde asset
    el('saveAssetBtn')?.addEventListener('click', () => {
        const name = el('assetName')?.value;
        const type = el('assetType')?.value;
        const ip = el('assetIp')?.value;
        const os = el('assetOs')?.value;
        const status = el('assetStatus')?.value;
        const id = el('assetId')?.value;
        
        if(!name || !type || !ip) return alert('Champs obligatoires');
        if(!validateIP(ip)) return alert('IP invalide');
        
        const asset = { 
            name, 
            type, 
            ip, 
            os: os || 'Non spécifié', 
            status, 
            lastScan: new Date().toLocaleDateString('fr-FR') 
        };
        
        if(id) {
            const idx = assets.findIndex(a => a.id == id);
            if(idx >= 0) assets[idx] = { ...assets[idx], ...asset };
        } else {
            assets.push({ id: nextId++, ...asset });
            if(window.AppData) AppData.nextAssetId = nextId;
        }
        if(window.AppData) AppData.assets = assets;
        render();
        modal?.hide();
    });

    // Paramètres
    el('saveSettingsBtn')?.addEventListener('click', () => {
        if(!el('settingsName') || !el('settingsEmail')) return;
        user.name = el('settingsName').value;
        user.email = el('settingsEmail').value;
        sessionStorage.setItem('user', JSON.stringify(user));
        if(window.AppData) AppData.currentUser = user;
        setText('userNameDisplay', user.name);
        setText('userEmailDisplay', user.email);
        setText('welcomeName', user.name.split(' ')[0]);
        alert('Paramètres enregistrés');
    });

    // Navigation sidebar
    document.querySelectorAll('.sidebar-menu a[data-section]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.sidebar-menu a').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            document.querySelectorAll('.content-section').forEach(s => s.classList.add('hidden'));
            el(link.dataset.section + 'Section')?.classList.remove('hidden');
        });
    });

    // Boutons ajout
    el('addAssetBtn')?.addEventListener('click', () => window.editAsset());
    el('addAssetBtn2')?.addEventListener('click', () => window.editAsset());

    // Déconnexion
    el('logoutBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        sessionStorage.removeItem('user');
        if(window.AppData) AppData.currentUser = null;
        window.location.href = 'index.html';
    });

    // Initial render
    render();
});