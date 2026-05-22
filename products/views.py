from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Exists, OuterRef, Value, BooleanField
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.pagination import paginate_queryset
from core.seo.breadcrumbs import build_breadcrumbs
from core.seo.faqs import faqs_for_category_slug, faqs_for_product
from core.seo.helpers import schema_json_ld_blocks
from core.seo.internal_links import related_for_product
from core.seo.schema import breadcrumb_list_json, faq_page_json, product_json
from core.services.guest_saves import guest_saved_ids, is_saved as guest_is_saved
from core.services.save_toggle import handle_save_toggle
from .models import Product, Category, SavedProducts


def _annotate_saved_products(products, request):
    if request.user.is_authenticated:
        saved_subquery = SavedProducts.objects.filter(
            user=request.user,
            product=OuterRef('pk'),
        )
        return products.annotate(is_saved=Exists(saved_subquery)), None
    guest_ids = set(guest_saved_ids(request, 'product'))
    return products.annotate(is_saved=Value(False, output_field=BooleanField())), guest_ids


def product_list(request):
    query = request.GET.get("q")
    category_slug = request.GET.get("category")
    subcategory_slug = request.GET.get("subcategory")

    products = Product.objects.filter(is_active=True).select_related(
        "category", "subcategory", "finish"
    ).order_by("category__name", "name")

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if subcategory_slug:
        products = products.filter(subcategory__slug=subcategory_slug)

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    products, guest_ids = _annotate_saved_products(products, request)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        page_obj, _ = paginate_queryset(products, request)
        products_data = []
        for p in page_obj:
            if guest_ids is not None:
                p.is_saved = p.id in guest_ids
            try:
                from core.images import thumbnail_url
                img = thumbnail_url(p.main_image, width=400) if p.main_image else None
            except Exception:
                img = p.main_image.url if p.main_image else None
            products_data.append({
                'id': p.id,
                'name': p.name,
                'url': p.get_absolute_url(),
                'main_image_url': img,
                'category_name': p.category.name,
                'subcategory_name': p.subcategory.name if p.subcategory else None,
                'finish': p.finish.name if p.finish else None,
                'description_excerpt': (
                    (p.description[:100] + '...') if len(p.description) > 100 else p.description
                ),
                'is_saved': p.is_saved,
            })
        return JsonResponse({
            'products': products_data,
            'page': page_obj.number,
            'num_pages': page_obj.paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        })

    page_obj, paginator = paginate_queryset(products, request)
    if guest_ids is not None:
        for p in page_obj:
            p.is_saved = p.id in guest_ids

    categories = Category.objects.prefetch_related('subcategories').all()
    breadcrumbs = build_breadcrumbs(request, ('Products', None))
    faq_items = faqs_for_category_slug(category_slug) if category_slug else []

    qs_parts = []
    if category_slug:
        qs_parts.append(f'category={category_slug}')
    if subcategory_slug:
        qs_parts.append(f'subcategory={subcategory_slug}')
    if query:
        qs_parts.append(f'q={query}')
    query_string = '&'.join(qs_parts)

    context = {
        "products": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "query_string": query_string,
        "categories": categories,
        "selected_category": category_slug,
        "selected_subcategory": subcategory_slug,
        "query": query or "",
        "breadcrumbs": breadcrumbs,
        "faq_items": faq_items,
        "schema_json_ld_blocks": schema_json_ld_blocks(
            breadcrumb_list_json(request, breadcrumbs),
            faq_page_json(faq_items),
        ),
    }
    return render(request, "products/product_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category', 'subcategory', 'finish').prefetch_related(
            'available_colors',
            'available_sizes',
            'safety_documents',
            'suitable_surfaces',
            'tools_needed',
            'related_products',
            'other_products_needed',
        ),
        slug=slug,
        is_active=True,
    )

    if request.user.is_authenticated:
        is_saved = SavedProducts.objects.filter(user=request.user, product=product).exists()
    else:
        is_saved = guest_is_saved(request, 'product', product.id)

    show_colors = product.category.features_colors
    show_sizes = product.category.features_sizes

    colors = product.available_colors.all().order_by('name') if show_colors else []
    sizes = product.available_sizes.all().order_by('name') if show_sizes else []
    documents = product.safety_documents.filter(is_active=True)
    surfaces = product.suitable_surfaces.all()
    tools = product.tools_needed.all()

    related_products = product.related_products.filter(is_active=True)
    other_products_needed = product.other_products_needed.filter(is_active=True)

    breadcrumbs = build_breadcrumbs(
        request,
        ('Products', 'product_list'),
        (product.category.name, 'product_list'),
        (product.name, None),
    )
    faq_items = faqs_for_product(product)

    context = {
        "product": product,
        "breadcrumbs": breadcrumbs,
        "faq_items": faq_items,
        "schema_json_ld_blocks": schema_json_ld_blocks(
            breadcrumb_list_json(request, breadcrumbs),
            product_json(request, product),
            faq_page_json(faq_items),
        ),
        "show_colors": show_colors,
        "show_sizes": show_sizes,
        "colors": colors,
        "sizes": sizes,
        "documents": documents,
        "surfaces": surfaces,
        "tools": tools,
        "related_products": related_products,
        "other_products_needed": other_products_needed,
        "is_saved": is_saved,
        **related_for_product(product),
    }
    return render(request, "products/product_detail.html", context)


@require_POST
def save_product_toggle(request):
    product_id = request.POST.get('product_id')
    if not product_id:
        return JsonResponse({'status': 'error', 'message': 'Product ID is required.'}, status=400)

    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found.'}, status=404)

    return handle_save_toggle(
        request,
        kind='product',
        item=product,
        saved_model=SavedProducts,
        relation_field='product',
    )
