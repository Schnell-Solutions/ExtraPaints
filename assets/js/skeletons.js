/**
 * Responsive card skeletons matching ExtraPaints grid layouts.
 * Reduces layout shift by mirroring final card dimensions.
 */
(function (global) {
  const B = (cls) => `<div class="ep-skel ${cls}" aria-hidden="true"></div>`;

  function columns(breakpoints) {
    const w = global.innerWidth || 1024;
    if (w >= 1280 && breakpoints.xl) return breakpoints.xl;
    if (w >= 1024 && breakpoints.lg) return breakpoints.lg;
    if (w >= 640 && breakpoints.sm) return breakpoints.sm;
    return breakpoints.default || 1;
  }

  function count(breakpoints, rows) {
    return columns(breakpoints) * (rows || 2);
  }

  const Skeletons = {
    columns,
    count,

    productCard() {
      return `
        <div class="ep-skeleton-card group bg-white rounded border border-neutral-200 flex flex-col overflow-hidden" aria-hidden="true">
          <div class="h-48 bg-neutral-100 relative rounded-t overflow-hidden flex items-center justify-center">
            ${B('w-24 h-24 rounded-md')}
            ${B('absolute top-3 right-3 w-8 h-8 rounded-full')}
          </div>
          <div class="p-5 flex flex-col flex-grow gap-3">
            <div class="flex gap-2">
              ${B('h-5 w-20 rounded')}
              ${B('h-5 w-16 rounded')}
            </div>
            ${B('h-6 w-3/4 max-w-[85%] rounded')}
            ${B('h-4 w-full rounded')}
            ${B('h-4 w-5/6 rounded')}
            <div class="flex justify-between items-center mt-auto pt-2">
              ${B('h-4 w-24 rounded')}
              ${B('h-9 w-16 rounded')}
            </div>
          </div>
        </div>`;
    },

    productGrid(n, extraClass) {
      const cls = extraClass || 'grid sm:grid-cols-2 lg:grid-cols-3 gap-4';
      return `<div class="${cls} ep-skeleton-grid" role="status" aria-label="Loading products">${Array.from({ length: n }, () => this.productCard()).join('')}</div>`;
    },

    productCards(n) {
      return Array.from({ length: n }, () => this.productCard()).join('');
    },

    colorCard() {
      return `
        <div class="ep-skeleton-card group bg-white rounded-md border border-neutral-200 flex flex-col overflow-hidden" aria-hidden="true">
          <div class="h-60 relative rounded-t-md overflow-hidden bg-neutral-100">
            ${B('absolute inset-0 w-full h-full')}
            ${B('absolute top-3 right-3 w-9 h-9 rounded-full')}
            ${B('absolute bottom-4 left-4 h-6 w-16 rounded-full')}
          </div>
          <div class="p-6 flex flex-col flex-grow gap-3">
            ${B('h-6 w-2/3 max-w-[90%] rounded')}
            <div class="flex items-center justify-between pt-4 mt-auto">
              ${B('h-6 w-24 rounded-full')}
              ${B('h-9 w-16 rounded')}
            </div>
          </div>
        </div>`;
    },

    colorGrid(n, extraClass) {
      const cls = extraClass || 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-12';
      return `<div class="${cls} ep-skeleton-grid" role="status" aria-label="Loading colors">${Array.from({ length: n }, () => this.colorCard()).join('')}</div>`;
    },

    colorCards(n) {
      return Array.from({ length: n }, () => this.colorCard()).join('');
    },

    ideaCard() {
      return `
        <div class="ep-skeleton-card group bg-white rounded-md border border-neutral-200 flex flex-col overflow-hidden" aria-hidden="true">
          <div class="relative">
            ${B('w-full h-64 rounded-t-md')}
            ${B('absolute top-3 right-3 w-10 h-10 rounded-full')}
          </div>
          <div class="p-5 flex flex-col gap-3">
            ${B('h-6 w-3/4 rounded')}
            ${B('h-4 w-full rounded')}
            ${B('h-4 w-2/3 rounded')}
            <div class="flex flex-wrap gap-2 pt-2">
              ${B('h-5 w-14 rounded-full')}
              ${B('h-5 w-20 rounded-full')}
            </div>
          </div>
        </div>`;
    },

    ideaGrid(n) {
      return `<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 ep-skeleton-grid" role="status" aria-label="Loading ideas">${Array.from({ length: n }, () => this.ideaCard()).join('')}</div>`;
    },

    ideaCards(n) {
      return Array.from({ length: n }, () => this.ideaCard()).join('');
    },

    portfolioCard() {
      return `
        <div class="ep-skeleton-card block bg-white rounded-md border border-neutral-200 overflow-hidden flex flex-col" aria-hidden="true">
          ${B('w-full h-60 rounded-t-md')}
          <div class="p-5 flex flex-col flex-grow gap-3">
            ${B('h-5 w-24 rounded')}
            ${B('h-6 w-3/4 rounded')}
            ${B('h-4 w-1/2 rounded mt-auto pt-2')}
          </div>
        </div>`;
    },

    portfolioGrid(n) {
      return `<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 ep-skeleton-grid" role="status" aria-label="Loading projects">${Array.from({ length: n }, () => this.portfolioCard()).join('')}</div>`;
    },

    portfolioCards(n) {
      return Array.from({ length: n }, () => this.portfolioCard()).join('');
    },

    productCarouselCard() {
      return `
        <div class="ep-skeleton-card flex-shrink-0 w-64 md:w-72 bg-white rounded-md border border-neutral-200 overflow-hidden snap-start" aria-hidden="true">
          ${B('h-48 md:h-56 w-full rounded-t-md')}
          <div class="p-4 md:p-5 flex flex-col gap-3">
            ${B('h-5 w-3/4 rounded')}
            ${B('h-10 w-full rounded-md mt-2')}
          </div>
        </div>`;
    },

    productCarousel(n) {
      return `<div class="flex overflow-x-auto space-x-4 md:space-x-6 pb-6 ep-skeleton-grid" role="status" aria-label="Loading products">${Array.from({ length: n }, () => this.productCarouselCard()).join('')}</div>`;
    },

    drawerProductCard() {
      return `
        <li class="ep-skeleton-card list-none">
          <div class="bg-white border border-gray-200 rounded-md p-4 shadow-sm mb-4">
            <div class="flex gap-4">
              ${B('w-20 h-20 flex-shrink-0 rounded-md')}
              <div class="flex-1 space-y-2 min-w-0">
                ${B('h-4 w-3/4 rounded')}
                ${B('h-3 w-1/2 rounded')}
                ${B('h-8 w-full rounded mt-2')}
              </div>
            </div>
            <div class="flex gap-2 mt-4 pt-3 border-t border-gray-100">
              ${B('h-9 flex-1 rounded-md')}
              ${B('h-9 flex-1 rounded-md')}
              ${B('h-9 w-10 rounded-md')}
            </div>
          </div>
        </li>`;
    },

    drawerProductList(n) {
      return Array.from({ length: n }, () => this.drawerProductCard()).join('');
    },

    searchColorRow() {
      return `
        <div class="flex items-center p-2 rounded-md gap-4 ep-skeleton-card" aria-hidden="true">
          ${B('w-8 h-8 rounded-full flex-shrink-0')}
          <div class="flex-1 space-y-2">
            ${B('h-4 w-32 rounded')}
            ${B('h-3 w-20 rounded')}
          </div>
        </div>`;
    },

    searchProductRow() {
      return `
        <div class="flex items-center p-2 rounded-md gap-4 ep-skeleton-card" aria-hidden="true">
          ${B('w-10 h-10 rounded-md flex-shrink-0')}
          <div class="flex-1 space-y-2">
            ${B('h-4 w-40 rounded')}
            ${B('h-3 w-24 rounded')}
          </div>
        </div>`;
    },

    searchResults() {
      return `
        <div class="ep-skeleton-search space-y-4" role="status" aria-label="Searching">
          ${B('h-4 w-24 rounded mb-2')}
          ${this.searchColorRow()}${this.searchColorRow()}${this.searchColorRow()}
          ${B('h-4 w-28 rounded mt-4 mb-2')}
          ${this.searchProductRow()}${this.searchProductRow()}${this.searchProductRow()}
        </div>`;
    },

    _fillGrid(container, cardsHtml, label) {
      container.innerHTML = cardsHtml;
      container.setAttribute('aria-busy', 'true');
      container.setAttribute('role', 'status');
      container.setAttribute('aria-label', label);
    },

    showProductGrid(container) {
      const n = count({ default: 1, sm: 2, lg: 3 }, 2);
      this._fillGrid(container, this.productCards(n), 'Loading products');
    },

    showColorGrid(container) {
      const n = count({ default: 1, sm: 2, lg: 3, xl: 4 }, 2);
      this._fillGrid(container, this.colorCards(n), 'Loading colors');
    },

    showIdeaGrid(container) {
      const n = count({ default: 1, sm: 2, lg: 3 }, 2);
      this._fillGrid(container, this.ideaCards(n), 'Loading ideas');
    },

    showPortfolioGrid(container) {
      const n = count({ default: 1, sm: 2, lg: 3 }, 2);
      this._fillGrid(container, this.portfolioCards(n), 'Loading projects');
    },

    showProductCarousel(container) {
      const n = count({ default: 2, sm: 3, lg: 4 }, 1);
      container.innerHTML = Array.from({ length: n }, () => this.productCarouselCard()).join('');
      container.setAttribute('aria-busy', 'true');
      container.setAttribute('role', 'status');
      container.setAttribute('aria-label', 'Loading products');
    },

    clearBusy(container) {
      if (!container) return;
      container.removeAttribute('aria-busy');
      container.removeAttribute('role');
      container.removeAttribute('aria-label');
    },

    staggerChildren(container) {
      if (!container || global.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      Array.from(container.children).forEach((el, i) => {
        if (el.classList.contains('col-span-full') || el.classList.contains('ep-skeleton-card')) return;
        el.classList.add('ep-card-enter');
        el.style.animationDelay = `${Math.min(i * 40, 200)}ms`;
      });
    },
  };

  global.ExtraPaintsSkeletons = Skeletons;
})(typeof window !== 'undefined' ? window : global);
