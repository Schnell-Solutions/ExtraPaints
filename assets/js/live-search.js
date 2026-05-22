/**
 * Live global search modal (fetch + render). Open/close/focus trap: accessibility.js
 */
(function () {
  const HEX_OK = /^#[0-9A-Fa-f]{6}$/;

  document.addEventListener('DOMContentLoaded', () => {
    const cfg = document.getElementById('extrapaints-live-search-config');
    if (!cfg) return;

    let searchUrl = '/ajax/live-search/';
    try {
      const data = JSON.parse(cfg.textContent);
      if (data.url) searchUrl = data.url;
    } catch (e) {
      /* use default */
    }

    const searchInput = document.getElementById('live-search-input');
    const resultsContainer = document.getElementById('search-results-container');
    const searchPlaceholder = document.getElementById('search-placeholder');
    if (!searchInput || !resultsContainer || !searchPlaceholder) return;

    let searchTimeout;
    const SEARCH_DELAY = 300;

    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimeout);
      const query = searchInput.value.trim();

      if (query.length < 2) {
        resultsContainer.replaceChildren();
        searchPlaceholder.textContent = 'Start typing to see results...';
        searchPlaceholder.classList.remove('hidden');
        return;
      }

      searchPlaceholder.classList.add('hidden');
      if (window.ExtraPaintsSkeletons) {
        resultsContainer.innerHTML = window.ExtraPaintsSkeletons.searchResults();
        resultsContainer.setAttribute('aria-busy', 'true');
      }
      searchTimeout = setTimeout(() => fetchResults(query, searchUrl), SEARCH_DELAY);
    });

    async function fetchResults(query, url) {
      try {
        const response = await fetch(`${url}?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        displayResults(data);
      } catch (error) {
        console.error('Live search failed:', error);
        resultsContainer.replaceChildren();
        const err = document.createElement('p');
        err.className = 'text-red-500 text-center py-8';
        err.textContent = 'An error occurred while searching.';
        resultsContainer.appendChild(err);
      }
    }

    function displayResults(data) {
      resultsContainer.replaceChildren();
      resultsContainer.removeAttribute('aria-busy');
      const totalResults = data.colors.length + data.products.length;

      if (totalResults === 0) {
        const p = document.createElement('p');
        p.className = 'text-gray-500 text-center py-8';
        p.textContent = `No results found for "${searchInput.value}".`;
        resultsContainer.appendChild(p);
        return;
      }

      if (data.colors.length > 0) {
        const h = document.createElement('h3');
        h.className = 'text-sm font-semibold text-primary-900 uppercase border-b pb-2 mb-2';
        h.textContent = `Colors (${data.colors.length})`;
        resultsContainer.appendChild(h);
        data.colors.forEach((color) => {
          const a = document.createElement('a');
          a.href = color.url;
          a.className =
            'flex items-center p-2 rounded-md hover:bg-primary-50 transition-colors ep-focus-ring';
          const sw = document.createElement('div');
          sw.className = 'w-8 h-8 rounded-full border border-gray-200 mr-4 flex-shrink-0';
          if (color.hex_code && HEX_OK.test(color.hex_code)) {
            sw.style.backgroundColor = color.hex_code;
          }
          const wrap = document.createElement('div');
          const t1 = document.createElement('p');
          t1.className = 'font-medium text-primary-900';
          t1.textContent = color.name;
          const t2 = document.createElement('p');
          t2.className = 'text-xs text-gray-500';
          t2.textContent = 'Code: ' + color.code;
          wrap.appendChild(t1);
          wrap.appendChild(t2);
          a.appendChild(sw);
          a.appendChild(wrap);
          resultsContainer.appendChild(a);
        });
      }

      if (data.products.length > 0) {
        if (data.colors.length > 0) {
          const spacer = document.createElement('div');
          spacer.className = 'pt-4 mt-4';
          resultsContainer.appendChild(spacer);
        }
        const h = document.createElement('h3');
        h.className = 'text-sm font-semibold text-primary-900 uppercase border-b pb-2 mb-2';
        h.textContent = `Products (${data.products.length})`;
        resultsContainer.appendChild(h);
        data.products.forEach((product) => {
          const a = document.createElement('a');
          a.href = product.url;
          a.className =
            'flex items-center p-2 rounded-md hover:bg-primary-50 transition-colors ep-focus-ring';
          const img = document.createElement('img');
          img.src = product.image_url;
          img.alt = product.name;
          img.className = 'w-10 h-10 object-cover rounded-md mr-4 flex-shrink-0';
          img.loading = 'lazy';
          const wrap = document.createElement('div');
          const t1 = document.createElement('p');
          t1.className = 'font-medium text-primary-900';
          t1.textContent = product.name;
          const t2 = document.createElement('p');
          t2.className = 'text-xs text-gray-500';
          t2.textContent = product.category;
          wrap.appendChild(t1);
          wrap.appendChild(t2);
          a.appendChild(img);
          a.appendChild(wrap);
          resultsContainer.appendChild(a);
        });
      }
    }
  });
})();
