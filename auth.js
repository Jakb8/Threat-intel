document.addEventListener('DOMContentLoaded', () => {
    const elements = {
        loginTab: document.getElementById('loginTab'),
        signupTab: document.getElementById('signupTab'),
        loginForm: document.getElementById('loginForm'),
        signupForm: document.getElementById('signupForm'),
        loginBtn: document.getElementById('loginBtn'),
        signupBtn: document.getElementById('signupBtn'),
        passwordInput: document.getElementById('signupPassword'),
        strengthBar: document.getElementById('strengthBar'),
        strengthText: document.getElementById('strengthText')
    };

    const switchTab = (activeTab, activeForm, hiddenTab, hiddenForm) => {
        activeTab.classList.add('active');
        hiddenTab.classList.remove('active');
        activeForm.classList.remove('hidden');
        hiddenForm.classList.add('hidden');
    };

    if (elements.loginTab) {
        elements.loginTab.addEventListener('click', () =>
            switchTab(elements.loginTab, elements.loginForm, elements.signupTab, elements.signupForm)
        );
    }

    if (elements.signupTab) {
        elements.signupTab.addEventListener('click', () =>
            switchTab(elements.signupTab, elements.signupForm, elements.loginTab, elements.loginForm)
        );
    }

    if (elements.loginBtn) {
        elements.loginBtn.addEventListener('click', () => {
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;

            if (!email || !password) {
                showToast('Veuillez remplir tous les champs', 'warning');
                return;
            }

            const user = AppData.users.find(u => u.email === email && u.password === password);

            if (user) {
                sessionStorage.setItem('user', JSON.stringify(user));
                AppData.currentUser = user;
                showToast('Connexion réussie ! Bienvenue ' + user.name, 'success');
                setTimeout(() => {
                    window.location.href = user.role === 'admin' ? 'dashboard.html' : 'ticketing.html';
                }, 500);
            } else {
                showToast('Email ou mot de passe incorrect', 'error');
            }
        });
    }

    if (elements.signupBtn) {
        elements.signupBtn.addEventListener('click', () => {
            const name = document.getElementById('signupName')?.value;
            const email = document.getElementById('signupEmail')?.value;
            const password = document.getElementById('signupPassword')?.value;
            const confirm = document.getElementById('confirmPassword')?.value;
            const terms = document.getElementById('acceptTerms')?.checked;

            if (!name || !email || !password || !confirm) {
                showToast('Remplissez tous les champs', 'warning');
                return;
            }

            if (password !== confirm) {
                showToast('Les mots de passe ne correspondent pas', 'error');
                return;
            }

            if (!terms) {
                showToast('Acceptez les conditions d\'utilisation', 'warning');
                return;
            }

            if (AppData.users.some(u => u.email === email)) {
                showToast('Cet email est déjà utilisé', 'error');
                return;
            }

            const newUser = {
                id: AppData.users.length + 1,
                name,
                email,
                password,
                role: 'client',
                phone: ''
            };

            AppData.users.push(newUser);
            sessionStorage.setItem('user', JSON.stringify(newUser));
            AppData.currentUser = newUser;
            showToast('Compte créé avec succès ! Bienvenue ' + name, 'success');
            setTimeout(() => {
                window.location.href = 'ticketing.html';
            }, 500);
        });
    }

    if (elements.passwordInput) {
        const strengthLevels = [
            { text: 'Entrez un mot de passe', class: '', width: '0' },
            { text: 'Mot de passe faible', class: 'weak', width: '33.33%' },
            { text: 'Mot de passe moyen', class: 'medium', width: '66.66%' },
            { text: 'Mot de passe fort', class: 'strong', width: '100%' }
        ];

        elements.passwordInput.addEventListener('input', function () {
            const password = this.value;

            if (password.length === 0) {
                elements.strengthBar.className = 'strength-bar';
                elements.strengthBar.style.width = '0';
                if (elements.strengthText) elements.strengthText.textContent = strengthLevels[0].text;
                return;
            }

            const hasLower = /[a-z]/.test(password);
            const hasUpper = /[A-Z]/.test(password);
            const hasNumber = /[0-9]/.test(password);
            const hasSpecial = /[$@#&!]/.test(password);
            const isLongEnough = password.length >= 8;

            const checks = [hasLower, hasUpper, hasNumber, hasSpecial, isLongEnough];
            const strength = checks.filter(Boolean).length;

            let level = 1;
            if (strength >= 4) level = 3;
            else if (strength >= 2) level = 2;

            elements.strengthBar.className = 'strength-bar';
            if (level > 0) elements.strengthBar.classList.add(strengthLevels[level].class);
            elements.strengthBar.style.width = strengthLevels[level].width;
            if (elements.strengthText) elements.strengthText.textContent = strengthLevels[level].text;
        });
    }
});
