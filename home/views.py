import json

# ProductVariant import is GONE
from django.db.models import Prefetch
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives

from colors.models import Color, SavedColor
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from ideas.models import SavedIdea
from products.models import Product, Category, SavedProducts
from .models import NewsletterSubscriber, Newsletter


def index(request):
    """
    View for the homepage, fetching products, categories, and colors.
    """

    # 1. Get all categories
    categories = Category.objects.all().order_by('name')
    category_names = [cat.name for cat in categories]

    # 2. Get all products, structured by category, for the JS

    # --- DELETED: variants_prefetch ---
    # We don't need to fetch variants or prices anymore.

    # --- UPDATED: all_products query ---
    # We just get the active products. No prefetch needed for variants.
    all_products = Product.objects.filter(is_active=True).select_related('category')

    # Build the product data dictionary in the *exact* structure the JS needs
    products_by_category = {cat_name: [] for cat_name in category_names}

    for product in all_products:
        # Ensure product's category is in our list
        if product.category.name not in products_by_category:
            continue

        # --- UPDATED: Image and Price Logic ---

        # We no longer need 'price_str'.
        image_url = ""  # Default empty

        # Use the product's main_image field
        if product.main_image:
            image_url = product.main_image.url
        else:
            # Fallback placeholder
            image_url = f"https://placehold.co/400x400/f1f5f9/9ca3af?text={product.name.replace(' ', '+')}"

        products_by_category[product.category.name].append({
            'id': product.id,
            'name': product.name,
            # 'price': key is GONE
            'img': image_url,
            'url': product.get_absolute_url()
        })

    # 3. Get "Most Loved" Colors (Unchanged, this is fine)
    most_loved_colors = Color.objects.filter(is_active=True).order_by('?')[:8]

    context = {
        'categories_json': category_names,
        'products_json': products_by_category,  # This JSON no longer contains price
        'most_loved_colors': most_loved_colors,
    }
    return render(request, 'home/index.html', context)


@login_required
def my_collection(request):
    """
    Displays all items saved by the current user in one dashboard.
    """

    # --- 1. Get Saved Products ---
    # Get the relation objects, but 'select' the related product
    # to avoid N+1 queries.
    saved_product_relations = SavedProducts.objects.filter(user=request.user) \
        .select_related('product') \
        .order_by('-saved_at')

    # Create a clean list of just the Product objects
    # We add .is_saved = True so the save-toggle button renders correctly.
    products = []
    for rel in saved_product_relations:
        product = rel.product
        product.is_saved = True  # We know it's saved
        products.append(product)

    # --- 2. Get Saved Colors ---
    saved_color_relations = SavedColor.objects.filter(user=request.user) \
        .select_related('color') \
        .order_by('-saved_at')

    colors = []
    for rel in saved_color_relations:
        color = rel.color
        color.is_saved = True  # We know it's saved
        colors.append(color)

    # --- 3. Get Saved Ideas ---
    # This view assumes your 'SavedIdea' model is set up just like the others
    saved_idea_relations = SavedIdea.objects.filter(user=request.user) \
        .select_related('idea') \
        .order_by('-saved_at')

    ideas = []
    for rel in saved_idea_relations:
        idea = rel.idea
        idea.is_saved = True  # We know it's saved
        ideas.append(idea)

    # --- 4. Send to template ---
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

        # --- Email Styling Logic ---
        html_content = render_to_string('home/simple_branded_email.html', {
            'subject': subject,
            'content': full_message,
            'site_name': 'ExtraPaints',
        })
        # ---------------------------

        try:
            msg = EmailMultiAlternatives(
                subject,
                full_message,  # Use plain text as the fallback body
                settings.DEFAULT_FROM_EMAIL,
                [settings.SALES_TEAM_EMAIL],  # Use the specialized sales team email
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
    AJAX view for live, global search across Colors and Products.
    """
    query = request.GET.get('q', '').strip()
    results = {'colors': [], 'products': []}

    if not query or len(query) < 2: # Only search if query is substantial
        return JsonResponse(results)

    # --- Search for Colors ---
    color_queryset = Color.objects.filter(
        Q(name__icontains=query) |
        Q(code__icontains=query) |
        Q(description__icontains=query),
        is_active=True
    )[:5] # Limit results for performance

    for color in color_queryset:
        results['colors'].append({
            'name': color.name,
            'code': color.code,
            'url': color.get_absolute_url(),
            'hex_code': color.hex_code # Assuming your Color model has a hex_code field
        })

    # --- Search for Products ---
    product_queryset = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query),
        is_active=True
    ).select_related('category')[:5] # Limit results for performance

    for product in product_queryset:
        # Use main_image or a fallback for the image
        image_url = product.main_image.url if product.main_image else 'https://placehold.co/40x40/f1f5f9/9ca3af?text=P'
        results['products'].append({
            'name': product.name,
            'category': product.category.name if product.category else 'Product',
            'url': product.get_absolute_url(),
            'image_url': image_url
        })

    return JsonResponse(results, safe=False)


@require_POST
def subscribe_newsletter(request):
    """
    Handles AJAX subscription form submission from the footer.
    """
    email = request.POST.get('email', '').strip()

    if not email:
        return JsonResponse({'status': 'error', 'message': 'Email is required.'}, status=400)

    try:
        # Attempt to create or find the subscriber
        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email
        )

        if created:
            message = "Thanks for subscribing! You'll receive our next newsletter."
            status = 'success'
        else:
            message = "You are already subscribed to our newsletter. Welcome back!"
            status = 'info'

        # Since this is an AJAX endpoint, return JSON
        return JsonResponse({'status': status, 'message': message})

    except Exception as e:
        # Log the exception (good practice)
        print(f"Subscription error: {e}")
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred. Please try again.'},
                            status=500)


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

