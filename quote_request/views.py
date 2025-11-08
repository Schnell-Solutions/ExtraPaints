from django.shortcuts import render

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from products.models import Product, Size
from colors.models import Color
from .quote import QuoteList  # Our new class


@require_POST
def add_to_quote(request):
    """
    Adds a product (with its selected color and size) to the quote list.
    This will be called by AJAX from the product detail page.
    """
    quote_list = QuoteList(request)

    try:
        product_id = request.POST.get('product_id')
        color_id = request.POST.get('color_id')
        size_id = request.POST.get('size_id')
        quantity = int(request.POST.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id)
        color = get_object_or_404(Color, id=color_id)
        size = get_object_or_404(Size, id=size_id)

        quote_list.add(product=product, color=color, size=size, quantity=quantity)

        return JsonResponse({
            'status': 'success',
            'message': 'Item added to quote list.',
            'quote_item_count': len(quote_list)
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def quote_detail(request):
    """
    This is the main "Quote List" page.
    It will show all the items and a form to submit the request.
    """
    # Assuming QuoteList is correctly imported and initialized
    quote_list = QuoteList(request)

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')

        items_summary = ""
        for item in quote_list:
            items_summary += (
                f"- {item['product'].name} "
                f"({item['color'].name}, {item['size'].name}) "
                f"x {item['quantity']}\n"
            )

        full_quote_request = (
            f"New Quote Request from: {name} ({email}, {phone})\n\n"
            f"Message: {message}\n\n"
            " TEMS REQUESTED ------------------------------\n"
            f" {items_summary}"
        )

        # --- Email Styling Logic ---
        subject = 'New Quote Request'
        html_content = render_to_string('quote_request/simple_branded_email.html', {
            'subject': subject,
            'content': full_quote_request,
            'site_name': 'ExtraPaints',
        })
        # ---------------------------

        try:
            msg = EmailMultiAlternatives(
                subject,
                full_quote_request,
                settings.DEFAULT_FROM_EMAIL,
                [settings.SALES_TEAM_EMAIL],  # Sends to sales team email
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

            # If the email sends successfully:
            quote_list.clear()
            messages.success(request, "Your quote request was successfully sent! We will contact you soon.")
            return render(request, 'quote_request/quote_submitted.html')

        except Exception as e:
            # If the email FAILS to send:
            print(f"Quote request email error: {e}")
            messages.error(request, "There was an error submitting your quote request. Please try again.")

            # IMPORTANT: Re-render the page showing the error message, but KEEP the items
            return render(request, 'quote_request/quote_detail.html', {'quote_list': quote_list})

    return render(request, 'quote_request/quote_detail.html', {'quote_list': quote_list})

@require_POST
def remove_from_quote(request):
    quote_list = QuoteList(request)
    item_key = request.POST.get('item_key')

    if item_key:
        quote_list.remove(item_key)

    return redirect('quote_detail')


@require_POST
def update_quote(request):
    """
    Updates the quantity of an item in the quote list.
    """
    quote_list = QuoteList(request)
    item_key = request.POST.get('item_key')

    try:
        # Get quantity, default to 1 if something goes wrong
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    if item_key:
        quote_list.update(item_key=item_key, quantity=quantity)

    return redirect('quote_detail')