"""Homepage product carousel catalog helpers."""

from products.models import Category, Product


def build_category_filters():
    """Return sorted filter button labels and lookup map for products."""
    main_categories = Category.objects.prefetch_related('subcategories').order_by('name')
    filter_names = []
    filter_map = {}

    for main_cat in main_categories:
        subs = main_cat.subcategories.all()
        if subs.exists():
            for sub in subs:
                filter_names.append(sub.name)
                filter_map[sub.name] = {'type': 'sub', 'obj': sub}
        else:
            filter_names.append(main_cat.name)
            filter_map[main_cat.name] = {'type': 'main', 'obj': main_cat}

    filter_names.sort()
    return filter_names, filter_map


def products_for_filter(filter_name, filter_map):
    """Serialize active products for one carousel filter label."""
    entry = filter_map.get(filter_name)
    if not entry:
        return []

    qs = Product.objects.filter(is_active=True).select_related('category', 'subcategory')
    if entry['type'] == 'sub':
        qs = qs.filter(subcategory=entry['obj'])
    else:
        qs = qs.filter(category=entry['obj'], subcategory__isnull=True)

    items = []
    for product in qs[:24]:
        if product.main_image:
            try:
                from core.images import thumbnail_url
                img = thumbnail_url(product.main_image, width=400)
            except Exception:
                img = product.main_image.url
        else:
            img = f'https://placehold.co/400x400/f1f5f9/9ca3af?text={product.name.replace(" ", "+")}'
        items.append({
            'id': product.id,
            'name': product.name,
            'img': img,
            'url': product.get_absolute_url(),
        })
    return items
