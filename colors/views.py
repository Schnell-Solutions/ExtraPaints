from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Prefetch, Exists, OuterRef, Value, BooleanField
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

# --- Import from products app to check product save status ---
from products.models import Product, Category, SavedProducts

# --- Import all our color models, including the new SavedColor ---
from .models import Color, ColorCollection, Finish, Surface, RoomType, SavedColor


def color_list(request):
    """
    Displays all active colors with dynamic filtering and search.
    """
    colors = Color.objects.filter(is_active=True)
    collections = ColorCollection.objects.all().order_by("name")
    finishes = Finish.objects.all().order_by("name")
    surfaces = Surface.objects.all().order_by("name")
    rooms = RoomType.objects.all().order_by("name")

    # --- Filters ---
    undertone = request.GET.get("undertone")
    collection_slug = request.GET.get("collection")
    finish_id = request.GET.get("finish")
    surface_id = request.GET.get("surface")
    room_id = request.GET.get("room")

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

    # --- Search ---
    query = request.GET.get("q")
    if query:
        colors = colors.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(description__icontains=query)
        )

    # --- Sort ---
    sort = request.GET.get("sort", "name")
    if sort == "newest":
        colors = colors.order_by("-created_at")
    elif sort == "lrv_high":
        colors = colors.order_by("-lrv")
    elif sort == "lrv_low":
        colors = colors.order_by("lrv")
    else:
        colors = colors.order_by("name")

    # --- Add 'is_saved' status (for colors) ---
    if request.user.is_authenticated:
        saved_subquery = SavedColor.objects.filter(
            user=request.user,
            color=OuterRef('pk')
        )
        colors = colors.annotate(is_saved=Exists(saved_subquery))
    else:
        colors = colors.annotate(is_saved=Value(False, output_field=BooleanField()))

    # --- Remove duplicates and pass to template ---
    return render(request, "colors/color_list.html", {
        "colors": colors.distinct(), # Pass the annotated, distinct queryset
        "collections": collections,
        "finishes": finishes,
        "surfaces": surfaces,
        "rooms": rooms,
        "selected_undertone": undertone,
        "selected_collection": collection_slug,
        "selected_finish": finish_id,
        "selected_surface": surface_id,
        "selected_room": room_id,
        "search_query": query or "",
        "sort": sort,
    })


def color_detail(request, slug):
    """
    Show detailed color information, and provide categories for the
    dynamic "Shop this Color" drawer.
    """
    color = get_object_or_404(
        Color.objects.prefetch_related(
            'available_finishes', 'recommended_surfaces',
            'recommended_rooms', 'inspiration_images'
        ),
        slug=slug,
        is_active=True # Good practice to check this here
    )

    # --- Check save status for this color ---
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedColor.objects.filter(user=request.user, color=color).exists()

    # --- Get all categories for the "Shop this Color" drawer ---
    all_categories = Category.objects.filter(
        products__available_colors=color,
        products__is_active=True # Only show categories that have active products
    ).distinct().order_by('name')

    context = {
        'color': color,
        'all_categories': all_categories,
        'is_saved': is_saved
    }
    return render(request, "colors/color_detail.html", context)


def ajax_get_color_products(request, color_id):
    """
    Fetches products for a specific color, optionally filtered by category.
    Now also includes the 'is_saved' status for each product.
    """
    try:
        color = Color.objects.get(id=color_id)
    except Color.DoesNotExist:
        return JsonResponse({'error': 'Color not found'}, status=404)

    selected_category_slug = request.GET.get('category')

    products_query = Product.objects.filter(
        available_colors=color,
        is_active=True
    ).prefetch_related(
        'available_sizes'
    ).select_related('category')

    if selected_category_slug:
        products_query = products_query.filter(category__slug=selected_category_slug)

    # --- Annotate with 'is_saved' status (for products) ---
    if request.user.is_authenticated:
        saved_product_subquery = SavedProducts.objects.filter(
            user=request.user,
            product=OuterRef('pk')
        )
        products_query = products_query.annotate(is_saved=Exists(saved_product_subquery))
    else:
        products_query = products_query.annotate(is_saved=Value(False, output_field=BooleanField()))


    products_query = products_query.order_by('name')

    products_data = []
    for product in products_query:
        if product.main_image:
            image_url = product.main_image.url
        else:
            # A fallback placeholder
            image_url = f"https://placehold.co/100x100/f1f5f9/9ca3af?text={product.name.replace(' ', '+')}"

        sizes = [{'id': size.id, 'name': size.name} for size in product.available_sizes.all()]

        product_info = {
            "id": product.id,
            "name": product.name,
            "url": product.get_absolute_url(),
            "image_url": image_url,
            "sizes": sizes,
            "is_saved": product.is_saved
        }
        products_data.append(product_info)

    return JsonResponse(products_data, safe=False)


@login_required
@require_POST
def save_color_toggle(request):
    """
    AJAX view to save or unsave a color for a user.
    """
    color_id = request.POST.get('color_id')
    if not color_id:
        return JsonResponse({'status': 'error', 'message': 'Color ID is required.'}, status=400)

    try:
        color = Color.objects.get(id=color_id)
    except Color.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Color not found.'}, status=404)

    # Find or create the saved item
    saved_obj, created = SavedColor.objects.get_or_create(
        user=request.user,
        color=color
    )

    if created:
        # We just saved it
        is_saved = True
    else:
        # It existed, so we delete it (unsave)
        saved_obj.delete()
        is_saved = False

    return JsonResponse({'status': 'success', 'is_saved': is_saved})

