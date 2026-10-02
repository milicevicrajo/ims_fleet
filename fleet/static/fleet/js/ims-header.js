(() => {
  const header = document.querySelector('.ims-header');
  if (!header) return;
  const switcher = header.querySelector('.ims-app-switcher');
  const panel = switcher.querySelector('.ims-app-panel');
  let closeTimer;
  const cancelClose = () => window.clearTimeout(closeTimer);
  switcher.addEventListener('pointerenter', (event) => {
    if (event.pointerType !== 'mouse') return;
    cancelClose();
    switcher.open = true;
  });
  switcher.addEventListener('pointerleave', (event) => {
    if (event.pointerType !== 'mouse') return;
    cancelClose();
    closeTimer = window.setTimeout(() => {
      if (!panel.contains(document.activeElement)) switcher.open = false;
    }, 150);
  });
  switcher.addEventListener('focusout', () => {
    window.setTimeout(() => {
      if (!switcher.contains(document.activeElement) && !switcher.matches(':hover')) {
        switcher.open = false;
      }
    }, 0);
  });
  const active = switcher.querySelector('.nav-link.active');
  if (active) {
    active.setAttribute('aria-current', 'page');
    header.querySelector('[data-current-module]').textContent = active.textContent.trim();
  }
  document.addEventListener('click', (event) => {
    if (!switcher.contains(event.target)) switcher.open = false;
  });
  header.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && switcher.open) {
      cancelClose();
      switcher.open = false;
      switcher.querySelector('summary').focus();
    }
  });
})();
