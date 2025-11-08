import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Exists, OuterRef, Value, BooleanField
from .models import Product, Category, SavedProducts
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST


def product_list(request):
    """
    Displays all active products, with filters and save status.
    """
    query = request.GET.get("q")
    category_slug = request.GET.get("category")

    products = Product.objects.filter(is_active=True).select_related("category")

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    categories = Category.objects.all()

    # --- Add 'is_saved' status ---
    if request.user.is_authenticated:
        saved_subquery = SavedProducts.objects.filter(
            user=request.user,
            product=OuterRef('pk')
        )
        products = products.annotate(is_saved=Exists(saved_subquery))
    else:
        products = products.annotate(is_saved=Value(False, output_field=BooleanField()))

    return render(request, "products/product_list.html", {
        "products": products,
        "categories": categories,
        "selected_category": category_slug,
        "query": query or "",
    })


def product_detail(request, slug):
    """
    Displays a single product, its colors, sizes, and save status.
    """
    product = get_object_or_404(
        Product.objects.prefetch_related(
            'available_colors', 'available_sizes', 'safety_documents'
        ),
        slug=slug,
        is_active=True
    )

    # --- Check save status for this product ---
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedProducts.objects.filter(user=request.user, product=product).exists()

    colors = product.available_colors.all().order_by('name')
    sizes = product.available_sizes.all().order_by('name')
    documents = product.safety_documents.filter(is_active=True)

    all_color_names = [color.name for color in colors]
    all_size_names = [size.name for size in sizes]

    color_availability_json = {
        color_name: all_size_names for color_name in all_color_names
    }
    size_availability_json = {
        size_name: all_color_names for size_name in all_size_names
    }

    context = {
        "product": product,
        "colors": colors,
        "sizes": sizes,
        "documents": documents,
        "is_saved": is_saved,
        "color_availability_json": color_availability_json, # Pass as JSON string
        "size_availability_json": size_availability_json,   # Pass as JSON string
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