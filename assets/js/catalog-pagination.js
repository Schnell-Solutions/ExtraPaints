/**
 * Update catalog list pagination after AJAX filter responses.
 */
(function () {
  function pageHref(page) {
    const url = new URL(window.location.href);
    if (page <= 1) {
      url.searchParams.delete('page');
    } else {
      url.searchParams.set('page', String(page));
    }
    return url.pathname + url.search;
  }

  function updateNav(container, meta) {
    if (!container || !meta) return;
    const page = meta.page || 1;
    const numPages = meta.num_pages || 1;
    if (numPages <= 1) {
      container.innerHTML = '';
      container.classList.add('hidden');
      return;
    }
    container.classList.remove('hidden');

    let html = '<nav class="mt-10 flex justify-center gap-2" aria-label="Pagination">';
    if (page > 1) {
      const prev = page - 1;
      html += `<a href="${pageHref(prev)}" data-ajax-page="${prev}" class="catalog-page-link px-4 py-2 rounded-md border border-gray-300 text-primary-900 hover:bg-primary-50 ep-focus-ring">Previous</a>`;
    }
    html += `<span class="px-4 py-2 text-gray-600 self-center">Page ${page} of ${numPages}</span>`;
    if (meta.has_next) {
      const next = page + 1;
      html += `<a href="${pageHref(next)}" data-ajax-page="${next}" class="catalog-page-link px-4 py-2 rounded-md border border-gray-300 text-primary-900 hover:bg-primary-50 ep-focus-ring">Next</a>`;
    }
    html += '</nav>';
    container.innerHTML = html;
  }

  window.ExtraPaintsPagination = {
    update(container, meta) {
      updateNav(container, meta);
    },
    bind(container, onPage) {
      if (!container) return;
      container.addEventListener('click', (e) => {
        const link = e.target.closest('.catalog-page-link');
        if (!link) return;
        e.preventDefault();
        const url = link.getAttribute('href');
        if (typeof onPage === 'function') {
          onPage(url);
        }
      });
    },
  };
})();
