/**
 * Focus trap for modals + restore focus on close.
 */
(function () {
  const FOCUSABLE =
    'a[href], button:not([disabled]), textarea, input:not([type="hidden"]), select, [tabindex]:not([tabindex="-1"])';

  function getFocusables(root) {
    return Array.from(root.querySelectorAll(FOCUSABLE)).filter(
      (el) => !el.closest('.ep-honeypot-wrap') && el.offsetParent !== null
    );
  }

  function trapFocus(modal, previousFocus) {
    const focusables = getFocusables(modal);
    if (!focusables.length) return () => {};
    const first = focusables[0];
    const last = focusables[focusables.length - 1];

    function onKeyDown(e) {
      if (e.key === 'Escape') {
        modal.dispatchEvent(new CustomEvent('ep-close-modal', { bubbles: true }));
        return;
      }
      if (e.key !== 'Tab') return;
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    modal.addEventListener('keydown', onKeyDown);
    first.focus();

    return () => {
      modal.removeEventListener('keydown', onKeyDown);
      if (previousFocus && typeof previousFocus.focus === 'function') {
        previousFocus.focus();
      }
    };
  }

  function wireModal(modal, openers, closer) {
    if (!modal) return;
    let release = null;
    let previousFocus = null;

    const open = () => {
      previousFocus = document.activeElement;
      modal.classList.remove('hidden');
      document.body.classList.add('ep-modal-open');
      release = trapFocus(modal, previousFocus);
    };

    const close = () => {
      modal.classList.add('hidden');
      document.body.classList.remove('ep-modal-open');
      if (modal.id === 'search-modal') {
        const input = modal.querySelector('#live-search-input');
        const results = modal.querySelector('#search-results-container');
        const placeholder = modal.querySelector('#search-placeholder');
        if (input) input.value = '';
        if (results) results.replaceChildren();
        if (placeholder) {
          placeholder.textContent = 'Start typing to see results...';
          placeholder.classList.remove('hidden');
        }
      }
      if (release) release();
      release = null;
    };

    openers.forEach((el) => {
      if (!el) return;
      el.addEventListener('click', (e) => {
        e.preventDefault();
        open();
      });
    });

    if (closer) closer.addEventListener('click', close);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) close();
    });
    modal.addEventListener('ep-close-modal', close);
  }

  document.addEventListener('DOMContentLoaded', () => {
    wireModal(
      document.getElementById('search-modal'),
      [
        document.getElementById('search-open-btn-desktop'),
        document.getElementById('search-open-btn-mobile'),
      ],
      document.getElementById('search-close-btn')
    );

    wireModal(
      document.getElementById('quick-inquiry-modal'),
      Array.from(document.querySelectorAll('[data-open-quick-inquiry]')),
      document.getElementById('quick-inquiry-close')
    );
  });
})();
