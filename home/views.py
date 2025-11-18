import json
from django.shortcuts import render, redirect
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib import messages
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

# --- Imported Models ---
from colors.models import Color, SavedColor
from ideas.models import SavedIdea
# NOTE: Ensure 'Category' here refers to your MainCategory model if you renamed it.
# Based on your previous requests, it seems 'Category' is now the main one.
from products.models import Product, Category, SubCategory, SavedProducts
from .models import NewsletterSubscriber, Newsletter


def index(request):
    """
    View for the homepage.
    Fetches categories for filter buttons.
    If a category has subcategories, it uses those for the filter buttons.
    If it doesn't, it uses the main category itself.
    """

    # 1. Fetch all main categories with their subcategories pre-fetched
    main_categories = Category.objects.prefetch_related('subcategories').order_by('name')

    # 2. Build the list of filter names (mixed main and sub categories)
    filter_names = []
    # We also need a mapping to know which filter name corresponds to which actual DB lookup later
    filter_map = {}

    for main_cat in main_categories:
        subs = main_cat.subcategories.all()
        if subs.exists():
            # If it has subcategories, add THEM to the filter list
            for sub in subs:
                filter_names.append(sub.name)
                filter_map[sub.name] = {'type': 'sub', 'obj': sub}
        else:
            # If no subcategories, add the MAIN category to the list
            filter_names.append(main_cat.name)
            filter_map[main_cat.name] = {'type': 'main', 'obj': main_cat}

    # Sort the combined list alphabetically for a neat display
    filter_names.sort()

    # 3. Get all active products
    all_products = Product.objects.filter(is_active=True).select_related('category', 'subcategory')

    # 4. Build product data dictionary based on our filter names
    products_by_filter = {name: [] for name in filter_names}

    for product in all_products:
        # Determine which filter this product belongs to
        filter_key = None
        if product.subcategory:
            # Try to match by subcategory name first
            if product.subcategory.name in products_by_filter:
                filter_key = product.subcategory.name
        else:
            # Fallback to main category name
            if product.category.name in products_by_filter:
                filter_key = product.category.name

        # If we found a valid filter bucket for this product, add it
        if filter_key:
            image_url = product.main_image.url if product.main_image else f"https://placehold.co/400x400/f1f5f9/9ca3af?text={product.name.replace(' ', '+')}"
            products_by_filter[filter_key].append({
                'id': product.id,
                'name': product.name,
                'img': image_url,
                'url': product.get_absolute_url()
            })

    # 5. Get "Most Loved" Colors
    most_loved_colors = Color.objects.filter(is_active=True).order_by('?')[:8]

    context = {
        # Pass the mixed list of category/subcategory names for buttons
        'categories_json': filter_names,
        # Pass the grouped product data keyed by those same names
        'products_json': products_by_filter,
        'most_loved_colors': most_loved_colors,
    }
    return render(request, 'home/index.html', context)


@login_required
def my_collection(request):
    """
    Displays all items saved by the current user.
    """
    saved_product_relations = SavedProducts.objects.filter(user=request.user) \
        .select_related('product', 'product__category') \
        .order_by('-saved_at')

    products = []
    for rel in saved_product_relations:
        product = rel.product
        product.is_saved = True
        products.append(product)

    saved_color_relations = SavedColor.objects.filter(user=request.user) \
        .select_related('color') \
        .order_by('-saved_at')

    colors = []
    for rel in saved_color_relations:
        color = rel.color
        color.is_saved = True
        colors.append(color)

    saved_idea_relations = SavedIdea.objects.filter(user=request.user) \
        .select_related('idea') \
        .order_by('-saved_at')

    ideas = []
    for rel in saved_idea_relations:
        idea = rel.idea
        idea.is_saved = True
        ideas.append(idea)

    context = {
        'saved_products': products,
        'saved_colors': colors,
        'saved_ideas': ideas,
    }
    return render(request, 'home/my_collection.html', context)


def about(request):
    return render(request, "home/about.html")


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        subject = f"New Contact Message from {name}"
        full_message = f"Sender Name: {name}\nSender Email: {email}\n\nMessage:\n{message}"

        html_content = render_to_string('home/simple_branded_email.html', {
            'subject': subject,
            'content': full_message,
            'site_name': 'ExtraPaints',
        })

        try:
            msg = EmailMultiAlternatives(
                subject,
                full_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.SALES_TEAM_EMAIL],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
            messages.success(request, "Your message has been sent successfully.")
        except Exception as e:
            print(f"Contact form email error: {e}")
            messages.error(request, "An error occurred while sending your message.")

        return redirect("contact")

    return render(request, "home/contact.html")


def live_search(request):
    """
    AJAX view for live global search.
    """
    query = request.GET.get('q', '').strip()
    results = {'colors': [], 'products': []}

    if not query or len(query) < 2:
        return JsonResponse(results)

    color_queryset = Color.objects.filter(
        Q(name__icontains=query) |
        Q(code__icontains=query) |
        Q(description__icontains=query),
        is_active=True
    )[:5]

    for color in color_queryset:
        results['colors'].append({
            'name': color.name,
            'code': color.code,
            'url': color.get_absolute_url(),
            'hex_code': color.hex_code
        })

    product_queryset = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query),
        is_active=True
    ).select_related('category', 'subcategory')[:5]

    for product in product_queryset:
        img_url = product.main_image.url if product.main_image else 'https://placehold.co/40x40/f1f5f9/9ca3af?text=P'

        cat_display = product.category.name
        if product.subcategory:
            cat_display += f" - {product.subcategory.name}"

        results['products'].append({
            'name': product.name,
            'category': cat_display,
            'url': product.get_absolute_url(),
            'image_url': img_url
        })

    return JsonResponse(results, safe=False)


@require_POST
def subscribe_newsletter(request):
    email = request.POST.get('email', '').strip()
    if not email:
        return JsonResponse({'status': 'error', 'message': 'Email is required.'}, status=400)
    try:
        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
        message = "Thanks for subscribing!" if created else "You are already subscribed."
        return JsonResponse({'status': 'success' if created else 'info', 'message': message})
    except Exception as e:
        print(f"Subscription error: {e}")
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred.'}, status=500)


# --- Email Sending Logic (Called by Admin Action) ---

def send_newsletter_email(newsletter):
    """
    Function to dispatch the newsletter email to all subscribers.
    """
    subscribers = NewsletterSubscriber.objects.all()
    recipient_list = [s.email for s in subscribers]

    # 1. Prepare HTML Content (or use a template)
    # NOTE: You need a template at 'home/newsletter_email.html' for this to work
    html_content = render_to_string('home/newsletter_email.html', {
        'subject': newsletter.subject,
        'body': newsletter.body,
        'site_name': 'Paint Company',  # Or settings.SITE_NAME
    })

    # 2. Prepare plain text fallback
    text_content = f"{newsletter.subject}\n\n{newsletter.body}"

    success_count = 0
    error_count = 0

    # Send the email
    try:
        # send_mail is simpler, but EmailMultiAlternatives supports HTML/Text
        msg = EmailMultiAlternatives(
            subject=newsletter.subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,  # Ensure this is set in settings.py
            to=recipient_list,
        )
        msg.attach_alternative(html_content, "text/html")

        # Django's mass email sending function
        success_count = msg.send(fail_silently=False)
        error_count = len(recipient_list) - success_count

    except Exception as e:
        # In a production app, you'd log this error
        error_count = len(recipient_list)
        print(f"Mass email sending failed: {e}")

    return success_count, error_count

