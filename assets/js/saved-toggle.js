/**
 * Shared save/unsave handler for products, colors, and ideas.
 * Expects #extrapaints-save-config JSON with toggle URLs.
 */
(function () {
  const configEl = document.getElementById('extrapaints-save-config');
  if (!configEl) return;

  let saveUrls;
  try {
    saveUrls = JSON.parse(configEl.textContent);
  } catch (e) {
    console.error('Invalid save toggle config', e);
    return;
  }

  const csrfInput = document.querySelector('input[name=csrfmiddlewaretoken]');
  const csrfToken = csrfInput ? csrfInput.value : '';

  const FILLED_HEART =
    '<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-red-500" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>';

  const OUTLINE_HEART =
    '<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>';

  const FILLED_HEART_SM =
    '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-red-500" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>';

  const OUTLINE_HEART_SM =
    '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>';

  function resolveToggle(btn) {
    if (btn.classList.contains('save-product-btn')) {
      return { url: saveUrls.product, field: 'product_id', id: btn.dataset.productId };
    }
    if (btn.classList.contains('save-color-btn')) {
      return { url: saveUrls.color, field: 'color_id', id: btn.dataset.colorId };
    }
    if (btn.classList.contains('save-idea-btn')) {
      return { url: saveUrls.idea, field: 'idea_id', id: btn.dataset.ideaId };
    }
    if (btn.classList.contains('js-save-toggle-btn')) {
      return {
        url: btn.dataset.url,
        field: btn.dataset.formKey,
        id: btn.dataset.itemId,
      };
    }
    return null;
  }

  function updateHeartUi(btn, isSaved) {
    const icon = btn.querySelector("[data-lucide='heart']");
    const text = btn.querySelector('.btn-save-text');
    const heartIcon = btn.querySelector('.heart-icon');
    const svg = btn.querySelector('svg');

    if (text) {
      text.textContent = isSaved ? 'Saved' : 'Save';
      if (icon) {
        if (isSaved) {
          icon.classList.add('fill-current', 'text-red-600');
          btn.classList.add('bg-red-100', 'text-red-700', 'border-red-200');
          btn.classList.remove('bg-white', 'text-gray-700', 'border-gray-300', 'hover:bg-gray-50');
        } else {
          icon.classList.remove('fill-current', 'text-red-600');
          btn.classList.remove('bg-red-100', 'text-red-700', 'border-red-200');
          btn.classList.add('bg-white', 'text-gray-700', 'border-gray-300', 'hover:bg-gray-50');
        }
      }
      return;
    }

    if (heartIcon) {
      const isSmall =
        btn.classList.contains('save-color-btn') ||
        btn.classList.contains('ep-drawer-save-btn');
      heartIcon.innerHTML = isSaved
        ? (isSmall ? FILLED_HEART_SM : FILLED_HEART)
        : (isSmall ? OUTLINE_HEART_SM : OUTLINE_HEART);
      btn.dataset.isSaved = isSaved ? 'true' : 'false';
      btn.title = isSaved ? 'Saved' : 'Add to favorites';
      if (btn.classList.contains('ep-drawer-save-btn')) {
        btn.classList.toggle('is-saved', !!isSaved);
      }
      return;
    }

    if (svg) {
      if (isSaved) {
        svg.setAttribute('fill', 'red');
        svg.setAttribute('stroke', 'red');
      } else {
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', 'currentColor');
      }
      btn.dataset.isSaved = isSaved ? 'true' : 'false';
    }
  }

  document.addEventListener('click', async (e) => {
    const btn = e.target.closest(
      '.save-product-btn, .save-color-btn, .save-idea-btn, .js-save-toggle-btn'
    );
    if (!btn || btn.disabled) return;

    const toggle = resolveToggle(btn);
    if (!toggle || !toggle.url || !toggle.field || !toggle.id) return;

    e.preventDefault();
    btn.disabled = true;

    const text = btn.querySelector('.btn-save-text');
    const originalText = text ? text.textContent : null;
    if (text) text.textContent = 'Updating...';

    const body = new URLSearchParams();
    body.append(toggle.field, toggle.id);
    if (csrfToken) body.append('csrfmiddlewaretoken', csrfToken);

    try {
      const res = await fetch(toggle.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: body.toString(),
      });
      const data = await res.json();
      if (data.status === 'success') {
        updateHeartUi(btn, data.is_saved);
      } else if (text) {
        text.textContent = 'Error';
        setTimeout(() => {
          text.textContent = originalText;
        }, 2000);
      }
    } catch (err) {
      console.error('Save toggle failed', err);
      if (text) {
        text.textContent = 'Error';
        setTimeout(() => {
          text.textContent = originalText;
        }, 2000);
      }
    } finally {
      btn.disabled = false;
    }
  });
})();
