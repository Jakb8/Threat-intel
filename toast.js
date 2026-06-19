function showToast(message, type = 'info', title = '') {
  const toastEl = document.getElementById('liveToast');
  const toastBody = document.getElementById('toastBody');
  const toastTitle = document.getElementById('toastTitle');
  if (!toastEl || !toastBody || !toastTitle) return;

  const header = toastEl.querySelector('.toast-header');
  header.className = 'toast-header';

  const config = {
    success: { bg: 'bg-success', icon: '✅', defaultTitle: 'Succès' },
    error: { bg: 'bg-danger', icon: '❌', defaultTitle: 'Erreur' },
    warning: { bg: 'bg-warning text-dark', icon: '⚠️', defaultTitle: 'Attention' },
    info: { bg: 'bg-info text-dark', icon: 'ℹ️', defaultTitle: 'Info' },
  };

  const c = config[type] || config.info;
  header.classList.add(c.bg);
  toastTitle.textContent = `${c.icon} ${title || c.defaultTitle}`;
  toastBody.textContent = message;

  const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
  toast.show();
}
