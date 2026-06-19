document.addEventListener('DOMContentLoaded', () => {
    const user = JSON.parse(sessionStorage.getItem('user') || 'null');
    if (!user || user.role !== 'admin') {
        showToast(user ? 'Accès restreint aux administrateurs' : 'Veuillez vous connecter', 'error');
        setTimeout(() => window.location.href = user ? 'ticketing.html' : 'auth.html', 800);
        return;
    }

    let { assets = [], tickets = [] } = window.AppData || {};
    let nextId = window.AppData?.nextAssetId || 5;
    const modal = document.getElementById('assetModal') ? new bootstrap.Modal(document.getElementById('assetModal')) : null;

    const el = id => document.getElementById(id);
    const setHTML = (id, html) => el(id) && (el(id).innerHTML = html);
    const setText = (id, text) => el(id) && (el(id).textContent = text);

    setText('userNameDisplay', user.name);
    setText('userEmailDisplay', user.email);
    setText('welcomeName', user.name.split(' ')[0]);
    if (el('settingsName')) el('settingsName').value = user.name;
    if (el('settingsEmail')) el('settingsEmail').value = user.email;

    const statusClass = s => ({ actif:'bg-success', inactif:'bg-secondary', vulnérable:'bg-danger', 'en scan':'bg-warning', maintenance:'bg-warning' }[s] || 'bg-secondary');
    const priorityColor = p => ({ basse:'#198754', moyenne:'#ffc107', haute:'#dc3545', critique:'#dc3545' }[p] || '#6c757d');
    const statusColor = s => ({ ouvert:'#ffc107', 'en cours':'#0dcaf0', résolu:'#198754', fermé:'#6c757d' }[s] || '#6c757d');
    const validateIP = ip => /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(ip);

    const emptyState = (cols, msg) =>
        `<tr><td colspan="${cols}" class="text-center py-5"><i class="bi bi-inbox fs-1 d-block mb-3 text-muted"></i><p class="text-muted mb-0">${msg}</p></td></tr>`;

    const render = () => {
        setHTML('assetsTableBody', assets.length
            ? assets.map(a => `<tr>
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
            </tr>`).join('')
            : emptyState(6, 'Aucun actif pour le moment'));
        setHTML('assetsFullTableBody', assets.length
            ? assets.map(a => `<tr>
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
            </tr>`).join('')
            : emptyState(7, 'Aucun actif enregistré'));
        setHTML('ticketsTableBody', tickets.length
            ? tickets.map(t => `<tr>
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
            </tr>`).join('')
            : emptyState(6, 'Aucun ticket de support'));

        setText('assetCount', assets.length);

        document.querySelectorAll('.priority').forEach(s => s.addEventListener('change', function () {
            const t = tickets.find(t => t.id == this.dataset.id);
            if (t) {
                t.priority = this.value;
                this.style.background = priorityColor(this.value);
                if (window.AppData) AppData.tickets = tickets;
                showToast(`Priorité mise à jour : ${this.value}`, 'info');
            }
        }));

        document.querySelectorAll('.status').forEach(s => s.addEventListener('change', function () {
            const t = tickets.find(t => t.id == this.dataset.id);
            if (t) {
                t.status = this.value;
                this.style.background = statusColor(this.value);
                if (window.AppData) AppData.tickets = tickets;
                showToast(`Statut mis à jour : ${this.value}`, 'info');
            }
        }));
    };

    window.editAsset = (id) => {
        const a = assets.find(a => a.id === id);
        if (a) {
            el('assetId').value = a.id;
            el('assetName').value = a.name;
            el('assetType').value = a.type;
            el('assetIp').value = a.ip;
            el('assetOs').value = a.os || '';
            el('assetStatus').value = a.status;
            el('modalTitle').textContent = 'Modifier l\'actif';
        } else {
            el('assetForm')?.reset();
            el('assetId').value = '';
            el('modalTitle').textContent = 'Ajouter un actif';
        }
        modal?.show();
    };

    window.deleteAsset = (id) => {
        const a = assets.find(a => a.id === id);
        if (!a) return;
        const confirmEl = document.getElementById('deleteConfirm');
        if (confirmEl) {
            document.getElementById('deleteConfirmBody').textContent = `Supprimer "${a.name}" ?`;
            confirmEl.dataset.targetId = id;
            new bootstrap.Modal(confirmEl).show();
        } else {
            assets = assets.filter(a => a.id !== id);
            if (window.AppData) AppData.assets = assets;
            render();
            showToast('Actif supprimé', 'success');
        }
    };

    window.scanAsset = (id) => {
        const a = assets.find(a => a.id === id);
        if (!a) return;

        const prev = a.status;
        a.status = 'en scan';
        render();
        showToast(`🔍 Scan lancé pour ${a.name}...`, 'info');

        setTimeout(() => {
            a.status = Math.random() < 0.3 ? 'vulnérable' : (prev === 'vulnérable' ? 'actif' : prev);
            a.lastScan = new Date().toLocaleDateString('fr-FR');
            render();
            if (a.status === 'vulnérable') {
                showToast(`⚠️ Vulnérabilités détectées sur ${a.name}`, 'warning');
            } else {
                showToast(`✅ Scan terminé pour ${a.name} — statut: ${a.status}`, 'success');
            }
        }, 2000);
    };

    window.assignTicket = (id) => {
        const t = tickets.find(t => t.id == id);
        if (!t) return;
        const users = AppData?.users?.filter(u => u.role !== 'admin') || [];
        if (users.length === 0) return showToast('Aucun utilisateur disponible', 'warning');

        const assignModal = document.getElementById('assignModal');
        if (assignModal) {
            const select = document.getElementById('assignSelect');
            select.innerHTML = users.map(u =>
                `<option value="${u.email}">${u.name} (${u.email})</option>`
            ).join('');
            assignModal.dataset.ticketId = id;
            new bootstrap.Modal(assignModal).show();
        } else {
            const email = prompt(`Assigner à :\n${users.map(u => `${u.name} (${u.email})`).join('\n')}\n\nEntrez l'email:`);
            if (email) {
                const u = users.find(u => u.email === email);
                if (u) {
                    t.assignedTo = email;
                    t.assignedToName = u.name;
                    if (window.AppData) AppData.tickets = tickets;
                    showToast(`Ticket assigné à ${u.name}`, 'success');
                } else {
                    showToast('Utilisateur non trouvé', 'error');
                }
            }
        }
    };

    window.confirmAssign = () => {
        const email = document.getElementById('assignSelect').value;
        const t = tickets.find(t => t.id == document.getElementById('assignModal').dataset.ticketId);
        const u = AppData?.users?.find(u => u.email === email);
        if (t && u) {
            t.assignedTo = email;
            t.assignedToName = u.name;
            if (window.AppData) AppData.tickets = tickets;
            showToast(`Ticket assigné à ${u.name}`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('assignModal')).hide();
        }
    };

    window.confirmDeleteAsset = () => {
        const id = parseInt(document.getElementById('deleteConfirm').dataset.targetId);
        assets = assets.filter(a => a.id !== id);
        if (window.AppData) AppData.assets = assets;
        render();
        bootstrap.Modal.getInstance(document.getElementById('deleteConfirm')).hide();
        showToast('Actif supprimé', 'success');
    };

    window.deleteTicket = (id) => {
        if (confirm('Supprimer ce ticket définitivement ?')) {
            tickets = tickets.filter(t => t.id != id);
            if (window.AppData) AppData.tickets = tickets;
            render();
            showToast('Ticket supprimé', 'success');
        }
    };

    el('saveAssetBtn')?.addEventListener('click', () => {
        const name = el('assetName')?.value;
        const type = el('assetType')?.value;
        const ip = el('assetIp')?.value;
        const os = el('assetOs')?.value;
        const status = el('assetStatus')?.value;
        const id = el('assetId')?.value;

        if (!name || !type || !ip) return showToast('Champs obligatoires : nom, type, IP', 'warning');
        if (!validateIP(ip)) return showToast('Adresse IP invalide', 'error');

        const asset = {
            name,
            type,
            ip,
            os: os || 'Non spécifié',
            status,
            lastScan: new Date().toLocaleDateString('fr-FR')
        };

        if (id) {
            const idx = assets.findIndex(a => a.id == id);
            if (idx >= 0) {
                assets[idx] = { ...assets[idx], ...asset };
                showToast('Actif modifié avec succès', 'success');
            }
        } else {
            assets.push({ id: nextId++, ...asset });
            if (window.AppData) AppData.nextAssetId = nextId;
            showToast('Actif ajouté avec succès', 'success');
        }
        if (window.AppData) AppData.assets = assets;
        render();
        modal?.hide();
    });

    el('saveSettingsBtn')?.addEventListener('click', () => {
        if (!el('settingsName') || !el('settingsEmail')) return;
        user.name = el('settingsName').value;
        user.email = el('settingsEmail').value;
        sessionStorage.setItem('user', JSON.stringify(user));
        if (window.AppData) AppData.currentUser = user;
        setText('userNameDisplay', user.name);
        setText('userEmailDisplay', user.email);
        setText('welcomeName', user.name.split(' ')[0]);
        showToast('Paramètres enregistrés', 'success');
    });

    document.querySelectorAll('.sidebar-menu a[data-section]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.sidebar-menu a').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            document.querySelectorAll('.content-section').forEach(s => {
                s.classList.add('hidden');
                s.style.opacity = '0';
            });
            const section = el(link.dataset.section + 'Section');
            if (section) {
                section.classList.remove('hidden');
                setTimeout(() => section.style.opacity = '1', 10);
            }
        });
    });

    el('addAssetBtn')?.addEventListener('click', () => window.editAsset());
    el('addAssetBtn2')?.addEventListener('click', () => window.editAsset());

    el('logoutBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        sessionStorage.removeItem('user');
        if (window.AppData) AppData.currentUser = null;
        showToast('Déconnexion réussie', 'info');
        setTimeout(() => window.location.href = 'index.html', 500);
    });

    const style = document.createElement('style');
    style.textContent = `
        .content-section {
            transition: opacity 0.3s ease;
        }
    `;
    document.head.appendChild(style);

    render();
});
