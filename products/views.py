import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Exists, OuterRef, Value, BooleanField
from .models import Product, Category, SubCategory, SavedProducts
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST


def product_list(request):
    """
    Displays all active products.
    Returns JSON data if requested via AJAX, otherwise renders full HTML.
    """
    query = request.GET.get("q")
    category_slug = request.GET.get("category")
    subcategory_slug = request.GET.get("subcategory")

    products = Product.objects.filter(is_active=True).select_related("category", "subcategory")

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if subcategory_slug:
        products = products.filter(subcategory__slug=subcategory_slug)

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    # --- Add 'is_saved' status ---
    if request.user.is_authenticated:
        saved_subquery = SavedProducts.objects.filter(
            user=request.user,
            product=OuterRef('pk')
        )
        products = products.annotate(is_saved=Exists(saved_subquery))
    else:
        products = products.annotate(is_saved=Value(False, output_field=BooleanField()))

    # --- AJAX JSON HANDLING ---
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        products_data = []
        for p in products:
            # Prepare data for JS to render the card
            products_data.append({
                'id': p.id,
                'name': p.name,
                'url': p.get_absolute_url(),
                # Use a placeholder if no image exists
                'main_image_url': p.main_image.url if p.main_image else None,
                'category_name': p.category.name,
                'subcategory_name': p.subcategory.name if p.subcategory else None,
                # Simple truncation for description if needed on the front-end card
                'description_excerpt': (p.description[:100] + '...') if len(p.description) > 100 else p.description,
                'is_saved': p.is_saved,
            })

        return JsonResponse({'products': products_data})

    # --- STANDARD FULL PAGE RENDER ---
    # Fetch categories for the sidebar only on full page load
    categories = Category.objects.prefetch_related('subcategories').all()

    context = {
        "products": products,
        "categories": categories,
        "selected_category": category_slug,
        "selected_subcategory": subcategory_slug,
        "query": query or "",
    }
    return render(request, "products/product_list.html", context)


def product_detail(request, slug):
    """
    Displays a single product. Adapts UI based on Category feature flags.
    """
    product = get_object_or_404(
        Product.objects.select_related('category', 'subcategory').prefetch_related(
            'available_colors', 'available_sizes', 'safety_documents'
        ),
        slug=slug,
        is_active=True
    )

    # --- Check save status ---
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedProducts.objects.filter(user=request.user, product=product).exists()

    # --- Feature Flags from Main Category ---
    show_colors = product.category.features_colors
    show_sizes = product.category.features_sizes

    # Only fetch if the category supports them
    colors = product.available_colors.all().order_by('name') if show_colors else []
    sizes = product.available_sizes.all().order_by('name') if show_sizes else []
    documents = product.safety_documents.filter(is_active=True)

    # --- Build Availability JSONs (useful if both colors and sizes exist) ---
    color_availability_json = {}
    size_availability_json = {}

    if show_colors and show_sizes:
         all_color_names = [c.name for c in colors]
         all_size_names = [s.name for s in sizes]
         # Simple cross-availability: assume all listed colors are available in all listed sizes for now
         color_availability_json = {c_name: all_size_names for c_name in all_color_names}
         size_availability_json = {s_name: all_color_names for s_name in all_size_names}

    context = {
        "product": product,
        "show_colors": show_colors,
        "show_sizes": show_sizes,
        "colors": colors,
        "sizes": sizes,
        "documents": documents,
        "is_saved": is_saved,
        "color_availability_json": color_availability_json,
        "size_availability_json": size_availability_json,
    }
    return render(request, "products/product_detail.html", context)


@login_required
@require_POST
def save_product_toggle(request):
    """
    AJAX view to save or unsave a product for a user.
    """
    product_id = request.POST.get('product_id')
    if not product_id:
        return JsonResponse({'status': 'error', 'message': 'Product ID is required.'}, status=400)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found.'}, status=404)

    saved_obj, created = SavedProducts.objects.get_or_create(
        user=request.user,
        product=product
    )

    if created:
        is_saved = True
    else:
        saved_obj.delete()
        is_saved = False

    return JsonResponse({'status': 'success', 'is_saved': is_saved})