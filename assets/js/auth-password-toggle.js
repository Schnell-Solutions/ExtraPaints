/**
 * Show/hide password fields on auth and account forms.
 */
(function () {
  function enhancePasswordField(input) {
    if (!input || input.type !== 'password' || input.closest('.ep-auth-password-wrap')) {
      return;
    }

    const wrap = document.createElement('div');
    wrap.className = 'ep-auth-password-wrap';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'ep-auth-password-toggle ep-focus-ring';
    btn.setAttribute('aria-label', 'Show password');
    btn.innerHTML =
      '<svg class="w-5 h-5 ep-icon-show" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>' +
      '<svg class="w-5 h-5 ep-icon-hide hidden" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-10-8-10-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 10 8 10 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';

    btn.addEventListener('click', () => {
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
      btn.querySelector('.ep-icon-show').classList.toggle('hidden', show);
      btn.querySelector('.ep-icon-hide').classList.toggle('hidden', !show);
    });

    wrap.appendChild(btn);
  }

  function init(root) {
    const scope = root || document;
    scope.querySelectorAll('input[type="password"]').forEach(enhancePasswordField);
  }

  document.addEventListener('DOMContentLoaded', () => init());

  window.ExtraPaintsAuth = { initPasswordToggles: init };
})();
