from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Exists, OuterRef, Value, BooleanField
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

# --- Import Models ---
# Note: Ensure 'products.models' imports match your actual model names.
# Based on previous context, 'Category' is now the Main Category.
from products.models import Product, Category, SavedProducts
from .models import Color, ColorCollection, Finish, Surface, RoomType, SavedColor


def color_list(request):
    """
    Displays all active colors with filters, search, sort, and save status.
    """
    # Start with active colors
    colors = Color.objects.filter(is_active=True)

    # Fetch filter options efficiently
    collections = ColorCollection.objects.all().order_by("name")
    finishes = Finish.objects.all().order_by("name")
    surfaces = Surface.objects.all().order_by("name")
    rooms = RoomType.objects.all().order_by("name")

    # --- GET Parameters ---
    undertone = request.GET.get("undertone")
    collection_slug = request.GET.get("collection")
    finish_id = request.GET.get("finish")
    surface_id = request.GET.get("surface")
    room_id = request.GET.get("room")
    query = request.GET.get("q")
    sort = request.GET.get("sort", "name")

    # --- Apply Filters ---
    if undertone in ["warm", "cool", "neutral"]:
        colors = colors.filter(undertone=undertone)
    if collection_slug:
        colors = colors.filter(collection__slug=collection_slug)
    if finish_id:
        colors = colors.filter(available_finishes__id=finish_id)
    if surface_id:
        colors = colors.filter(recommended_surfaces__id=surface_id)
    if room_id:
        colors = colors.filter(recommended_rooms__id=room_id)
    if query:
        colors = colors.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(description__icontains=query)
        )

    # --- Apply Sorting ---
    if sort == "newest":
        colors = colors.order_by("-created_at")
    elif sort == "lrv_high":
        colors = colors.order_by("-lrv")
    elif sort == "lrv_low":
        colors = colors.order_by("lrv")
    else:
        colors = colors.order_by("name")

    # --- Annotate 'is_saved' status ---
    if request.user.is_authenticated:
        is_saved_subquery = SavedColor.objects.filter(
            user=request.user,
            color=OuterRef('pk')
        )
        colors = colors.annotate(is_saved=Exists(is_saved_subquery))
    else:
        colors = colors.annotate(is_saved=Value(False, output_field=BooleanField()))


    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        colors_data = []
        for c in colors:
            colors_data.append({
                'id': c.id,
                'name': c.name,
                'code': c.code,
                'hex_code': c.hex_code,
                # Use a placeholder if standard image is missing and no hex code exists
                'image_url': c.main_image.url if c.main_image else '/static/images/default.jpg',
                'collection_name': c.collection.name if c.collection else None,
                'url': c.get_absolute_url(),
                'is_saved': c.is_saved,
            })
        return JsonResponse({'colors': colors_data})

    # Render with distinct results to avoid duplicates from many-to-many filters
    context = {
        "colors": colors.distinct(),
        "collections": collections,
        "finishes": finishes,
        "surfaces": surfaces,
        "rooms": rooms,
        # Pass back selected filters to keep UI state
        "selected_undertone": undertone,
        "selected_collection": collection_slug,
        "selected_finish": finish_id,
        "selected_surface": surface_id,
        "selected_room": room_id,
        "search_query": query or "",
        "sort": sort,
    }
    return render(request, "colors/color_list.html", context)


def color_detail(request, slug):
    """
    Shows color details and fetches Main Categories for the "Shop this Color" drawer.
    """
    color = get_object_or_404(
        Color.objects.prefetch_related(
            'available_finishes', 'recommended_surfaces',
            'recommended_rooms', 'inspiration_images'
        ),
        slug=slug,
        is_active=True
    )

    # --- 1. Check if user saved this color ---
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedColor.objects.filter(user=request.user, color=color).exists()

    # --- 2. Fetch Main Categories for "Shop this Color" ---
    # We only want main categories (e.g., "Paints") that have active products
    # available in THIS specific color.
    shop_categories = Category.objects.filter(
        products__available_colors=color,
        products__is_active=True
    ).distinct().order_by('name')

    context = {
        'color': color,
        'is_saved': is_saved,
        'shop_categories': shop_categories,  # Renamed for clarity
    }
    return render(request, "colors/color_detail.html", context)


def ajax_get_color_products(request, color_id):
    """
    AJAX: Fetches products for a specific color.
    Supports filtering by Main Category slug.
    """
    try:
        color = Color.objects.get(id=color_id, is_active=True)
    except Color.DoesNotExist:
        return JsonResponse({'error': 'Color not found or inactive'}, status=404)

    # Get optional main category filter from AJAX request
    category_slug = request.GET.get('category')

    # Base query: Active products available in this color
    products = Product.objects.filter(
        available_colors=color,
        is_active=True
    ).select_related('category', 'subcategory').prefetch_related('available_sizes')

    # Apply category filter if provided
    if category_slug:
        products = products.filter(category__slug=category_slug)

    # --- Annotate 'is_saved' for products ---
    if request.user.is_authenticated:
        saved_prod_subquery = SavedProducts.objects.filter(
            user=request.user,
            product=OuterRef('pk')
        )
        products = products.annotate(is_saved=Exists(saved_prod_subquery))
    else:
        products = products.annotate(is_saved=Value(False, output_field=BooleanField()))

    # Order and prepare JSON response
    products = products.order_by('category__name', 'name')

    products_data = []
    for p in products:
        # Determine image URL with fallback
        img_url = p.main_image.url if p.main_image else "/media/default.jpg"

        # Build simple list of available sizes
        sizes_list = [{'id': s.id, 'name': s.name} for s in p.available_sizes.all()]

        products_data.append({
            "id": p.id,
            "name": p.name,
            "category": p.category.name,
            # Show subcategory if it exists, else just main category
            "full_category": f"{p.category.name} - {p.subcategory.name}" if p.subcategory else p.category.name,
            "url": p.get_absolute_url(),
            "image_url": img_url,
            "sizes": sizes_list,
            "is_saved": p.is_saved
        })

    return JsonResponse(products_data, safe=False)


@login_required
@require_POST
def save_color_toggle(request):
    """
    AJAX: Toggles the saved status of a color for the logged-in user.
    """
    color_id = request.POST.get('color_id')
    if not color_id:
        return JsonResponse({'status': 'error', 'message': 'Color ID required'}, status=400)

    try:
        color = Color.objects.get(id=color_id)
        # get_or_create returns (obj, created_boolean)
        saved_obj, created = SavedColor.objects.get_or_create(
            user=request.user,
            color=color
        )

        if created:
            return JsonResponse({'status': 'success', 'is_saved': True})
        else:
            # If it wasn't created, it already existed, so we delete it (toggle off)
            saved_obj.delete()
            return JsonResponse({'status': 'success', 'is_saved': False})

    except Color.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Color not found'}, status=404)
    except Exception as e:
        # Catch-all for other potential DB errors
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)