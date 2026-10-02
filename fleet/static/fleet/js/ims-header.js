(() => {
  const header = document.querySelector('.ims-header');
  if (!header) return;
  const switcher = header.querySelector('.ims-app-switcher');
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
      switcher.open = false;
      switcher.querySelector('summary').focus();
    }
  });
})();
