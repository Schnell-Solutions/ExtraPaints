from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Exists, OuterRef, Value, BooleanField
from django.views.decorators.http import require_POST

from core.pagination import paginate_queryset
from core.seo.breadcrumbs import build_breadcrumbs
from core.seo.helpers import schema_json_ld_blocks
from core.seo.internal_links import related_for_color
from core.seo.schema import breadcrumb_list_json
from core.services.guest_saves import guest_saved_ids, is_saved as guest_is_saved
from core.services.save_toggle import handle_save_toggle
from products.models import Product, Category, SavedProducts
from .models import Color, ColorCollection, RoomType, SavedColor


def color_list(request):
    colors = Color.objects.filter(is_active=True)

    collections = ColorCollection.objects.all().order_by("name")
    rooms = RoomType.objects.all().order_by("name")

    undertone = request.GET.get("undertone")
    collection_slug = request.GET.get("collection")
    room_id = request.GET.get("room")
    query = request.GET.get("q")
    sort = request.GET.get("sort", "name")

    if undertone in ["warm", "cool", "neutral"]:
        colors = colors.filter(undertone=undertone)
    if collection_slug:
        colors = colors.filter(collection__slug=collection_slug)
    if room_id:
        colors = colors.filter(recommended_rooms__id=room_id)
    if query:
        colors = colors.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(description__icontains=query)
        )

    if sort == "newest":
        colors = colors.order_by("-created_at")
    elif sort == "lrv_high":
        colors = colors.order_by("-lrv")
    elif sort == "lrv_low":
        colors = colors.order_by("lrv")
    else:
        colors = colors.order_by("name")

    colors = colors.distinct()

    if request.user.is_authenticated:
        is_saved_subquery = SavedColor.objects.filter(
            user=request.user,
            color=OuterRef('pk'),
        )
        colors = colors.annotate(is_saved=Exists(is_saved_subquery))
        guest_color_ids = None
    else:
        colors = colors.annotate(is_saved=Value(False, output_field=BooleanField()))
        guest_color_ids = set(guest_saved_ids(request, 'color'))

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        page_obj, _ = paginate_queryset(colors, request)
        colors_data = []
        for c in page_obj:
            if guest_color_ids is not None:
                c.is_saved = c.id in guest_color_ids
            try:
                from core.images import thumbnail_url
                img = (
                    thumbnail_url(c.main_image, width=400)
                    if c.main_image
                    else staticfiles_storage.url('images/extrapaints.jpg')
                )
            except Exception:
                img = c.main_image.url if c.main_image else staticfiles_storage.url('images/extrapaints.jpg')
            colors_data.append({
                'id': c.id,
                'name': c.name,
                'code': c.code,
                'hex_code': c.hex_code,
                'image_url': img,
                'collection_name': c.collection.name if c.collection else None,
                'url': c.get_absolute_url(),
                'is_saved': c.is_saved,
            })
        return JsonResponse({
            'colors': colors_data,
            'page': page_obj.number,
            'num_pages': page_obj.paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        })

    page_obj, paginator = paginate_queryset(colors, request)
    if guest_color_ids is not None:
        for c in page_obj:
            c.is_saved = c.id in guest_color_ids

    breadcrumbs = build_breadcrumbs(request, ('Colors', None))
    qs_parts = []
    if undertone:
        qs_parts.append(f'undertone={undertone}')
    if collection_slug:
        qs_parts.append(f'collection={collection_slug}')
    if room_id:
        qs_parts.append(f'room={room_id}')
    if query:
        qs_parts.append(f'q={query}')
    if sort and sort != 'name':
        qs_parts.append(f'sort={sort}')

    context = {
        "colors": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "query_string": '&'.join(qs_parts),
        "collections": collections,
        "rooms": rooms,
        "selected_undertone": undertone,
        "selected_collection": collection_slug,
        "selected_room": room_id,
        "search_query": query or "",
        "sort": sort,
        "breadcrumbs": breadcrumbs,
        "schema_json_ld_blocks": schema_json_ld_blocks(
            breadcrumb_list_json(request, breadcrumbs),
        ),
    }
    return render(request, "colors/color_list.html", context)


def color_detail(request, slug):
    color = get_object_or_404(
        Color.objects.prefetch_related('recommended_rooms', 'inspiration_images'),
        slug=slug,
        is_active=True,
    )

    if request.user.is_authenticated:
        is_saved = SavedColor.objects.filter(user=request.user, color=color).exists()
    else:
        is_saved = guest_is_saved(request, 'color', color.id)

    shop_categories = Category.objects.filter(
        products__available_colors=color,
        products__is_active=True,
    ).distinct().order_by('name')

    breadcrumbs = build_breadcrumbs(
        request,
        ('Colors', 'color_list'),
        (color.name, None),
    )
    context = {
        'color': color,
        'is_saved': is_saved,
        'shop_categories': shop_categories,
        'breadcrumbs': breadcrumbs,
        'schema_json_ld_blocks': schema_json_ld_blocks(
            breadcrumb_list_json(request, breadcrumbs),
        ),
        **related_for_color(color),
    }
    return render(request, 'colors/color_detail.html', context)


def ajax_get_color_products(request, color_id):
    try:
        color = Color.objects.get(id=color_id, is_active=True)
    except Color.DoesNotExist:
        return JsonResponse({'error': 'Color not found or inactive'}, status=404)

    category_slug = request.GET.get('category')

    products = Product.objects.filter(
        available_colors=color,
        is_active=True,
    ).select_related('category', 'subcategory', 'finish').prefetch_related('available_sizes')

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if request.user.is_authenticated:
        saved_prod_subquery = SavedProducts.objects.filter(
            user=request.user,
            product=OuterRef('pk'),
        )
        products = products.annotate(is_saved=Exists(saved_prod_subquery))
        guest_product_ids = None
    else:
        products = products.annotate(is_saved=Value(False, output_field=BooleanField()))
        guest_product_ids = set(guest_saved_ids(request, 'product'))

    products = products.order_by('category__name', 'name')

    products_data = []
    for p in products:
        if guest_product_ids is not None:
            p.is_saved = p.id in guest_product_ids
        try:
            from core.images import thumbnail_url
            img = (
                thumbnail_url(p.main_image, width=400)
                if p.main_image
                else staticfiles_storage.url('images/extrapaints.jpg')
            )
        except Exception:
            img = p.main_image.url if p.main_image else staticfiles_storage.url('images/extrapaints.jpg')
        sizes_list = [{'id': s.id, 'name': s.name} for s in p.available_sizes.all()]

        products_data.append({
            "id": p.id,
            "name": p.name,
            "category": p.category.name,
            "full_category": f"{p.category.name} - {p.subcategory.name}" if p.subcategory else p.category.name,
            "finish": p.finish.name if p.finish else "",
            "url": p.get_absolute_url(),
            "image_url": img,
            "sizes": sizes_list,
            "is_saved": p.is_saved,
        })

    return JsonResponse(products_data, safe=False)


@require_POST
def save_color_toggle(request):
    color_id = request.POST.get('color_id')
    if not color_id:
        return JsonResponse({'status': 'error', 'message': 'Color ID required'}, status=400)

    try:
        color = Color.objects.get(id=color_id, is_active=True)
    except Color.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Color not found'}, status=404)

    return handle_save_toggle(
        request,
        kind='color',
        item=color,
        saved_model=SavedColor,
        relation_field='color',
    )
