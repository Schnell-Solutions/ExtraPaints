(function () {

  const configEl = document.getElementById('home-page-config');

  if (!configEl) return;



  let config;

  try {

    config = JSON.parse(configEl.textContent);

  } catch (e) {

    console.error('Invalid home page config', e);

    return;

  }



  function toggleView(view) {

    const listBtn = document.getElementById('listBtn');

    const mapBtn = document.getElementById('mapBtn');

    const listView = document.getElementById('listView');

    const mapView = document.getElementById('mapView');

    if (!listBtn || !mapBtn || !listView || !mapView) return;



    const activeClasses = ['bg-primary-900', 'text-white'];

    const inactiveClasses = ['bg-white', 'text-primary-900'];



    if (view === 'list') {

      listView.classList.remove('hidden');

      mapView.classList.add('hidden');

      listBtn.classList.add(...activeClasses);

      listBtn.classList.remove(...inactiveClasses);

      mapBtn.classList.remove(...activeClasses);

      mapBtn.classList.add(...inactiveClasses);

    } else {

      mapView.classList.remove('hidden');

      listView.classList.add('hidden');

      mapBtn.classList.add(...activeClasses);

      mapBtn.classList.remove(...inactiveClasses);

      listBtn.classList.remove(...activeClasses);

      listBtn.classList.add(...inactiveClasses);

    }

  }

  window.toggleView = toggleView;



  document.addEventListener('DOMContentLoaded', () => {

    const box = document.getElementById('hero-color-link');

    const nameSpan = document.getElementById('hero-color-name');

    const codeSpan = document.getElementById('hero-color-code');

    const image = document.getElementById('hero-image');

    const secondaryImage = document.getElementById('hero-image-secondary');



    if (config.randomHeroColorUrl) {

      const INTERVAL_TIME = 600000;

      let nextColorData = null;



      async function prepareNextColor() {

        try {

          const response = await fetch(config.randomHeroColorUrl);

          if (response.ok) nextColorData = await response.json();

        } catch (error) {

          console.warn('Background hero color fetch failed', error);

        }

      }



      function applyNextColor() {

        if (!nextColorData) return;

        if (box) box.style.borderColor = nextColorData.hex;

        if (image) image.style.borderColor = nextColorData.hex;

        if (secondaryImage) secondaryImage.style.borderColor = nextColorData.hex;

        if (nameSpan) nameSpan.textContent = nextColorData.name;

        if (codeSpan) codeSpan.textContent = nextColorData.code;

        if (box) box.href = nextColorData.url;

        nextColorData = null;

        prepareNextColor();

      }



      prepareNextColor();

      setInterval(applyNextColor, INTERVAL_TIME);

    }



    const categoriesEl = document.getElementById('categories-data');

    if (!categoriesEl || !config.homeProductsUrl) return;



    const categories = JSON.parse(categoriesEl.textContent);

    const categoryFilterContainer = document.getElementById('category-filters');

    const productRowContainer = document.getElementById('product-row-container');

    const productCache = new Map();



    toggleView('list');



    const S = window.ExtraPaintsSkeletons;



    function renderCategoryFilters() {

      if (!categoryFilterContainer) return;

      if (!Array.isArray(categories) || categories.length === 0) {

        categoryFilterContainer.innerHTML = '';

        if (productRowContainer) {

          productRowContainer.innerHTML =

            '<div class="text-center py-12 border-2 border-dashed border-neutral-300 rounded-md bg-neutral-50 w-full mx-4"><p class="text-neutral-600 ep-lead font-medium">Our product catalog is coming soon.</p></div>';

        }

        return;

      }



      categoryFilterContainer.innerHTML = categories

        .map((categoryName, index) => {

          const isActive = categoryName === config.initialCategory || (index === 0 && !config.initialCategory);

          return `<button type="button" class="category-btn px-4 py-2 md:px-6 md:py-2.5 rounded-md text-xs md:text-sm font-bold tracking-wide transition-all duration-200 border whitespace-nowrap ep-focus-ring ${

            isActive

              ? 'bg-primary-900 text-white border-primary-900 shadow hover:bg-primary-800'

              : 'bg-white text-neutral-700 border-neutral-200 hover:border-primary-900 hover:text-primary-900'

          }" data-category="${categoryName}">${categoryName}</button>`;

        })

        .join('');

    }



    function renderProducts(products) {

      if (!productRowContainer) return;

      productRowContainer.innerHTML = '';

      if (S) S.clearBusy(productRowContainer);



      if (!products.length) {

        productRowContainer.innerHTML =

          '<div class="text-center py-10 px-4 border-2 border-dashed border-neutral-200 rounded-md bg-white w-full mx-4"><p class="text-neutral-500 ep-lead font-medium">No products found in this category yet.</p></div>';

        return;

      }



      products.forEach((product) => {

        const card = document.createElement('div');

        card.className =

          'flex-shrink-0 w-64 md:w-72 bg-white rounded-md border border-neutral-200 overflow-hidden hover:shadow transition-all duration-300 group snap-start';

        card.style.opacity = '0';

        card.style.transform = 'translateY(10px)';

        card.innerHTML = `

          <div class="relative h-48 md:h-56 bg-neutral-100 overflow-hidden">

            <a href="${product.url}" class="block h-full w-full">

              <img src="${product.img}" alt="${product.name}" width="400" height="300" class="w-full h-full object-contain p-6 transition-transform duration-500 group-hover:scale-110" loading="lazy" decoding="async">

            </a>

          </div>

          <div class="p-4 md:p-5 flex flex-col">

            <h3 class="text-base md:text-lg font-bold text-neutral-800 mb-1 line-clamp-1">

              <a href="${product.url}" class="hover:text-primary-900 transition-colors">${product.name}</a>

            </h3>

            <a href="${product.url}" class="mt-4 w-full inline-flex justify-center items-center px-4 py-2 md:py-2.5 bg-primary-900 text-white text-xs md:text-sm font-bold rounded-md hover:bg-primary-800 transition-colors ep-focus-ring">View Details</a>

          </div>`;

        productRowContainer.appendChild(card);

        requestAnimationFrame(() => {

          card.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out';

          card.style.opacity = '1';

          card.style.transform = 'translateY(0)';

        });

      });

    }



    async function loadProducts(categoryName) {

      if (productCache.has(categoryName)) {

        renderProducts(productCache.get(categoryName));

        return;

      }

      if (S) S.showProductCarousel(productRowContainer);

      try {

        const res = await fetch(`${config.homeProductsUrl}?category=${encodeURIComponent(categoryName)}`);

        const data = await res.json();

        const list = data.products || [];

        productCache.set(categoryName, list);

        renderProducts(list);

      } catch (err) {

        console.error('Home products fetch failed', err);

        productRowContainer.innerHTML =

          '<div class="text-center py-10 text-red-600">Could not load products. Please refresh.</div>';

      }

    }



    if (categoryFilterContainer) {

      categoryFilterContainer.addEventListener('click', (e) => {

        const btn = e.target.closest('.category-btn');

        if (!btn) return;

        const ACTIVE = ['bg-primary-900', 'text-white', 'border-primary-900', 'shadow-md'];

        const INACTIVE = ['bg-white', 'text-neutral-700', 'border-neutral-200'];

        categoryFilterContainer.querySelectorAll('.category-btn').forEach((b) => {

          b.classList.remove(...ACTIVE);

          b.classList.add(...INACTIVE);

        });

        btn.classList.remove(...INACTIVE);

        btn.classList.add(...ACTIVE);

        loadProducts(btn.dataset.category);

      });

    }



    renderCategoryFilters();

    if (config.initialCategory) {

      loadProducts(config.initialCategory);

    }



    const scrollContainer = document.getElementById('product-row-container');

    const leftBtn = document.getElementById('scroll-left');

    const rightBtn = document.getElementById('scroll-right');

    if (scrollContainer && leftBtn && rightBtn) {

      leftBtn.setAttribute('aria-label', 'Scroll products left');

      rightBtn.setAttribute('aria-label', 'Scroll products right');

      const scrollAmount = 320;

      leftBtn.addEventListener('click', () => scrollContainer.scrollBy({ left: -scrollAmount, behavior: 'smooth' }));

      rightBtn.addEventListener('click', () => scrollContainer.scrollBy({ left: scrollAmount, behavior: 'smooth' }));

      const updateButtons = () => {

        const maxScroll = scrollContainer.scrollWidth - scrollContainer.clientWidth;

        leftBtn.classList.toggle('opacity-0', scrollContainer.scrollLeft <= 10);

        leftBtn.classList.toggle('pointer-events-none', scrollContainer.scrollLeft <= 10);

        rightBtn.classList.toggle('opacity-0', scrollContainer.scrollLeft >= maxScroll - 10);

        rightBtn.classList.toggle('pointer-events-none', scrollContainer.scrollLeft >= maxScroll - 10);

      };

      scrollContainer.addEventListener('scroll', updateButtons);

      setTimeout(updateButtons, 100);

      new MutationObserver(updateButtons).observe(scrollContainer, { childList: true });

    }

  });

})();


