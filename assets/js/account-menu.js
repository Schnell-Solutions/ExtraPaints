/**
 * Account dropdown in the main navbar (logged-in users).
 */
(function () {
  document.addEventListener('DOMContentLoaded', () => {
    const wrap = document.getElementById('account-menu-wrap');
    const btn = document.getElementById('account-menu-btn');
    const menu = document.getElementById('account-menu-dropdown');
    if (!wrap || !btn || !menu) return;

    const close = () => {
      menu.classList.add('hidden');
      btn.setAttribute('aria-expanded', 'false');
    };

    const open = () => {
      menu.classList.remove('hidden');
      btn.setAttribute('aria-expanded', 'true');
      if (typeof lucide !== 'undefined') lucide.createIcons();
    };

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = !menu.classList.contains('hidden');
      if (isOpen) close();
      else open();
    });

    document.addEventListener('click', (e) => {
      if (!wrap.contains(e.target)) close();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') close();
    });
  });
})();
