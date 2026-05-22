import logging
import random
import re

from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST

from core.forms import ContactForm, QuickInquiryForm
from core.services.email import InquiryEmailService
from core.services.guest_saves import guest_saved_ids
from core.services.inquiry import confirm_to_customer, notify_sales
from core.services.rate_limit import rate_limit

logger = logging.getLogger(__name__)

# --- Imported Models ---
from colors.models import Color, SavedColor
from ideas.models import SavedIdea
# NOTE: Ensure 'Category' here refers to your MainCategory model if you renamed it.
# Based on your previous requests, it seems 'Category' is now the main one.
from products.models import Product, Category, SubCategory, SavedProducts
from home.catalog import build_category_filters, products_for_filter
from .models import NewsletterSubscriber, Newsletter


def _random_active_color_with_hex():
    """Pick one random color without using ORDER BY RANDOM() (expensive at scale)."""
    qs = Color.objects.filter(
        is_active=True,
        hex_code__isnull=False,
    ).exclude(hex_code='')
    ids = list(qs.values_list('pk', flat=True)[:2500])
    if not ids:
        return None
    return qs.filter(pk=random.choice(ids)).first()


def robots_txt(request):
    """Dynamic robots.txt so sitemap URL matches the deployed host or PUBLIC_SITE_URL."""
    base = (getattr(settings, 'PUBLIC_SITE_URL', '') or '').rstrip('/')
    if not base:
        base = request.build_absolute_uri('/').rstrip('/')
    body = (
        'User-agent: *\n'
        'Disallow: /admin/\n'
        'Disallow: /accounts/\n'
        'Disallow: /quote/\n'
        'Disallow: /save-toggle/\n'
        'Disallow: /ajax/\n'
        'Disallow: /colors/save-toggle/\n'
        'Disallow: /products/save-toggle/\n'
        'Disallow: /ideas/save-toggle/\n'
        f'Sitemap: {base}/sitemap.xml\n'
    )
    return HttpResponse(body, content_type='text/plain')


def index(request):
    """Homepage — category labels only; products load via AJAX to keep HTML payload small."""
    filter_names, _filter_map = build_category_filters()

    most_loved_colors = Color.objects.filter(is_active=True).order_by('-updated_at')[:8]
    initial_color = _random_active_color_with_hex()
    initial_category = filter_names[0] if filter_names else ''

    context = {
        'categories_json': filter_names,
        'initial_category': initial_category,
        'hero_color': initial_color,
        'most_loved_colors': most_loved_colors,
    }
    return render(request, 'home/index.html', context)


def home_products_api(request):
    """Return carousel products for one homepage category filter (cached client-side)."""
    category = request.GET.get('category', '').strip()
    filter_names, filter_map = build_category_filters()
    if category not in filter_map:
        return JsonResponse({'products': []})
    return JsonResponse({
        'category': category,
        'products': products_for_filter(category, filter_map),
    })


def get_random_hero_color(request):
    color = _random_active_color_with_hex()

    if color:
        return JsonResponse({
            'name': color.name,
            'code': color.code,
            'hex': color.hex_code,
            'url': color.get_absolute_url()
        })
    return JsonResponse({'error': 'No colors found'}, status=404)


def my_collection(request):
    """Saved items for signed-in users (database) or guests (session)."""
    if request.user.is_authenticated:
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
    else:
        product_ids = guest_saved_ids(request, 'product')
        color_ids = guest_saved_ids(request, 'color')
        idea_ids = guest_saved_ids(request, 'idea')

        products = list(
            Product.objects.filter(id__in=product_ids, is_active=True)
            .select_related('category', 'subcategory')
        )
        for product in products:
            product.is_saved = True

        colors = list(Color.objects.filter(id__in=color_ids, is_active=True))
        for color in colors:
            color.is_saved = True

        from ideas.models import Idea
        ideas = list(Idea.objects.filter(id__in=idea_ids, is_active=True).select_related('category'))
        for idea in ideas:
            idea.is_saved = True

    context = {
        'saved_products': products,
        'saved_colors': colors,
        'saved_ideas': ideas,
        'is_guest_collection': not request.user.is_authenticated,
    }
    return render(request, 'home/my_collection.html', context)


def about(request):
    from core.seo.breadcrumbs import build_breadcrumbs
    from core.seo.helpers import schema_json_ld_blocks
    from core.seo.schema import breadcrumb_list_json

    breadcrumbs = build_breadcrumbs(request, ('About Us', None))
    return render(request, 'home/about.html', {
        'breadcrumbs': breadcrumbs,
        'schema_json_ld_blocks': schema_json_ld_blocks(
            breadcrumb_list_json(request, breadcrumbs),
        ),
    })


@rate_limit('contact')
def contact(request):
    from affiliates.services import (
        process_referral_on_post,
        record_referral_lead,
        referral_email_line,
        posted_referral_code,
    )

    form = ContactForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            affiliate, referral_invalid = process_referral_on_post(request)
            if referral_invalid:
                return render(request, 'home/contact.html', {
                    'form': form,
                    'referral_invalid': True,
                    'referral_value': posted_referral_code(request),
                })

            cd = form.cleaned_data
            phone_line = f"\nPhone: {cd['phone']}" if cd.get('phone') else ''
            full_message = (
                f"Sender Name: {cd['name']}\n"
                f"Sender Email: {cd['email']}{phone_line}\n\n"
                f"Message:\n{cd['message']}"
                f"{referral_email_line(affiliate)}"
            )
            subject = f"New Contact Message from {cd['name']}"
            if notify_sales(subject=subject, text_body=full_message):
                record_referral_lead(
                    affiliate=affiliate,
                    lead_type='contact',
                    customer_name=cd['name'],
                    customer_email=cd['email'],
                    customer_phone=cd.get('phone', ''),
                    message_excerpt=(cd['message'] or '')[:500],
                    request=request,
                )
                confirm_to_customer(
                    email=cd['email'],
                    subject='We received your message — ExtraPaints',
                    template='home/customer_confirmation.html',
                    context={
                        'headline': 'Thank you for contacting us',
                        'body': (
                            'Our sales team has received your inquiry and will respond '
                            'within one business day.'
                        ),
                        'plain_text': 'We received your message and will respond soon.',
                    },
                )
                messages.success(
                    request,
                    'Your message was sent. Check your email for a confirmation — we typically respond within 24 hours.',
                )
            else:
                messages.error(request, 'An error occurred while sending your message.')
            return redirect('contact')
        messages.error(request, 'Please correct the errors below.')

    return render(request, 'home/contact.html', {'form': form})


@require_POST
@rate_limit('quick_inquiry')
def quick_inquiry(request):
    from affiliates.services import (
        process_referral_on_post,
        record_referral_lead,
        referral_email_line,
        posted_referral_code,
    )

    form = QuickInquiryForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {'status': 'error', 'message': 'Please fill in all required fields correctly.'},
            status=400,
        )

    affiliate, referral_invalid = process_referral_on_post(request)
    if referral_invalid:
        return JsonResponse({
            'status': 'referral_invalid',
            'message': (
                'The referral code entered could not be found. '
                'You may continue without a referral code or correct the code.'
            ),
            'referral_value': posted_referral_code(request),
        }, status=400)

    cd = form.cleaned_data
    ref = cd.get('project_reference') or 'Not specified'
    full_message = (
        f"Quick inquiry from: {cd['name']}\n"
        f"Phone: {cd['phone']}\n"
        f"Product / project: {ref}"
        f"{referral_email_line(affiliate)}"
    )
    subject = f"Quick Inquiry from {cd['name']}"
    if notify_sales(subject=subject, text_body=full_message):
        record_referral_lead(
            affiliate=affiliate,
            lead_type='quick_inquiry',
            customer_name=cd['name'],
            customer_phone=cd['phone'],
            message_excerpt=ref[:500],
            request=request,
        )
        return JsonResponse({
            'status': 'success',
            'message': f'Thanks {cd["name"]}! Our team will call you shortly. {request.build_absolute_uri("/")}',
        })
    return JsonResponse(
        {'status': 'error', 'message': 'Could not send your inquiry. Please call us directly.'},
        status=500,
    )


@rate_limit('live_search', limit=60, period=60, methods=('GET',))
def live_search(request):
    """
    AJAX view for live global search.
    """
    hex_ok = re.compile(r"^#[0-9A-Fa-f]{6}$")
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
        hx = (color.hex_code or "").strip()
        if hx and not hex_ok.match(hx):
            hx = ""
        results['colors'].append({
            'name': color.name,
            'code': color.code,
            'url': color.get_absolute_url(),
            'hex_code': hx,
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


def privacy_policy(request):
    return render(request, 'home/legal/privacy.html')


def terms_conditions(request):
    return render(request, 'home/legal/terms.html')


@require_POST
@rate_limit('newsletter', limit=5, period=600)
def subscribe_newsletter(request):
    email = request.POST.get('email', '').strip()
    if not email:
        return JsonResponse({'status': 'error', 'message': 'Email is required.'}, status=400)
    try:
        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
        message = "Thanks for subscribing!" if created else "You are already subscribed."
        return JsonResponse({'status': 'success' if created else 'info', 'message': message})
    except Exception:
        logger.exception('Newsletter subscription error')
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred.'}, status=500)


# --- Email Sending Logic (Called by Admin Action) ---

def send_newsletter_email(newsletter):
    """Dispatch newsletter to subscribers in BCC batches."""
    from core.services.newsletter import send_newsletter_batched

    return send_newsletter_batched(newsletter)

