(function () {
  const form = document.getElementById('quick-inquiry-form');
  const msgEl = document.getElementById('quick-inquiry-message');
  const invalidPanel = document.getElementById('qi-referral-invalid');
  const skipBtn = document.getElementById('qi-skip-referral');
  const fixBtn = document.getElementById('qi-fix-referral');
  const referralInput = document.getElementById('qi-referral');

  if (!form) return;

  const csrfInput = form.querySelector('[name=csrfmiddlewaretoken]');

  if (skipBtn) {
    skipBtn.addEventListener('click', () => {
      if (referralInput) referralInput.value = '';
      if (invalidPanel) invalidPanel.classList.add('hidden');
      const hidden = document.getElementById('qi-skip-referral-flag');
      if (hidden) hidden.value = '1';
      else {
        const inp = document.createElement('input');
        inp.type = 'hidden';
        inp.name = 'skip_referral';
        inp.value = '1';
        inp.id = 'qi-skip-referral-flag';
        form.appendChild(inp);
      }
      form.requestSubmit();
    });
  }

  if (fixBtn) {
    fixBtn.addEventListener('click', () => {
      if (invalidPanel) invalidPanel.classList.add('hidden');
      if (referralInput) referralInput.focus();
    });
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById('quick-inquiry-submit');
    if (msgEl) {
      msgEl.classList.remove('hidden');
      msgEl.textContent = 'Sending…';
      msgEl.className = 'text-sm text-gray-600';
    }
    if (submitBtn) submitBtn.disabled = true;

    try {
      const res = await fetch(form.dataset.action || '/ajax/quick-inquiry/', {
        method: 'POST',
        body: new FormData(form),
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfInput ? csrfInput.value : '',
        },
      });
      const data = await res.json();

      if (data.status === 'referral_invalid') {
        if (invalidPanel) invalidPanel.classList.remove('hidden');
        if (msgEl) {
          msgEl.textContent = data.message || 'Referral code not found.';
          msgEl.className = 'text-sm text-amber-800';
        }
        return;
      }

      if (data.status === 'success') {
        if (msgEl) {
          msgEl.textContent = data.message;
          msgEl.className = 'text-sm text-green-700';
        }
        form.reset();
        const modal = document.getElementById('quick-inquiry-modal');
        if (modal) {
          setTimeout(() => modal.dispatchEvent(new CustomEvent('ep-close-modal')), 2500);
        }
      } else {
        if (msgEl) {
          msgEl.textContent = data.message || 'Something went wrong.';
          msgEl.className = 'text-sm text-red-600';
        }
      }
    } catch (err) {
      if (msgEl) {
        msgEl.textContent = 'Network error. Please try again or call us.';
        msgEl.className = 'text-sm text-red-600';
      }
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  });
})();
