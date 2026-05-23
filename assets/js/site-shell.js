/**
 * Sitewide shell: mobile nav drawer, newsletter form, goBack helper.
 */
(function () {
  function getCsrfToken() {
    const input = document.querySelector('input[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
  }

  function initMobileNavDrawer() {
    const menuBtn = document.getElementById('mobile-menu-button');
    const closeBtn = document.getElementById('mobile-nav-close-btn');
    const overlay = document.getElementById('mobile-nav-overlay');
    const panel = document.getElementById('mobile-nav-panel');

    if (!menuBtn || !overlay || !panel) {
      return;
    }

    let isOpen = false;

    function setMenuIcon(open) {
      const icon = menuBtn.querySelector('i');
      if (!icon) return;
      icon.setAttribute('data-lucide', open ? 'x' : 'menu');
      try {
        if (typeof lucide !== 'undefined') lucide.createIcons();
      } catch (err) {
        /* ignore */
      }
    }

    function setOpen(open) {
      if (open === isOpen) return;
      isOpen = open;

      menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      menuBtn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      setMenuIcon(open);

      if (open) {
        overlay.classList.remove('hidden');
        panel.classList.remove('hidden');
        overlay.setAttribute('aria-hidden', 'false');
        panel.setAttribute('aria-hidden', 'false');

        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            overlay.classList.add('is-visible');
            panel.classList.add('is-open');
          });
        });

        document.body.classList.add('ep-drawer-scroll-lock');
        try {
          if (typeof lucide !== 'undefined') lucide.createIcons();
        } catch (err) {
          /* ignore */
        }
      } else {
        overlay.classList.remove('is-visible');
        panel.classList.remove('is-open');
        panel.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('ep-drawer-scroll-lock');

        const onPanelClosed = (e) => {
          if (e.target !== panel || e.propertyName !== 'transform') return;
          panel.removeEventListener('transitionend', onPanelClosed);
          overlay.classList.add('hidden');
          panel.classList.add('hidden');
          overlay.setAttribute('aria-hidden', 'true');
        };
        panel.addEventListener('transitionend', onPanelClosed);
      }
    }

    menuBtn.addEventListener('click', (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      setOpen(!isOpen);
    });

    if (closeBtn) {
      closeBtn.addEventListener('click', (ev) => {
        ev.preventDefault();
        setOpen(false);
      });
    }

    overlay.addEventListener('click', () => setOpen(false));

    panel.querySelectorAll('[data-close-mobile-nav]').forEach((el) => {
      el.addEventListener('click', () => setOpen(false));
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && isOpen) setOpen(false);
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initMobileNavDrawer();

    const newsletterForm = document.getElementById('newsletter-form');
    const newsletterMessage = document.getElementById('newsletter-message');
    const newsletterSubmitBtn = document.getElementById('newsletter-submit-btn');
    const newsletterEmailInput = document.getElementById('newsletter-email-input');

    if (newsletterForm && newsletterSubmitBtn && newsletterMessage) {
      newsletterForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        newsletterSubmitBtn.disabled = true;
        newsletterMessage.textContent = 'Processing...';
        newsletterMessage.className = 'mt-2 text-sm font-medium text-primary-300';

        const formData = new FormData(newsletterForm);
        formData.append('csrfmiddlewaretoken', getCsrfToken());

        try {
          const response = await fetch(newsletterForm.action, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
          });
          const data = await response.json();

          if (data.status === 'success') {
            newsletterMessage.textContent = data.message;
            newsletterMessage.className = 'mt-2 text-sm font-medium text-green-400';
            if (newsletterEmailInput) newsletterEmailInput.value = '';
          } else if (data.status === 'info') {
            newsletterMessage.textContent = data.message;
            newsletterMessage.className = 'mt-2 text-sm font-medium text-yellow-400';
          } else {
            newsletterMessage.textContent = data.message || 'An error occurred.';
            newsletterMessage.className = 'mt-2 text-sm font-medium text-red-400';
          }
        } catch (error) {
          newsletterMessage.textContent = 'Network error. Please try again.';
          newsletterMessage.className = 'mt-2 text-sm font-medium text-red-400';
        } finally {
          newsletterSubmitBtn.disabled = false;
        }
      });
    }

    if (typeof lucide !== 'undefined') {
      lucide.createIcons();
    }
  });

  window.goBack = function goBack(fallbackUrl) {
    const fallback =
      fallbackUrl ||
      document.querySelector('[data-back-fallback]')?.getAttribute('href') ||
      '/';

    try {
      const ref = document.referrer;
      if (ref) {
        const refOrigin = new URL(ref).origin;
        if (refOrigin === window.location.origin) {
          history.back();
          return;
        }
      }
    } catch (err) {
      /* ignore invalid referrer */
    }

    window.location.href = fallback;
  };
})();
