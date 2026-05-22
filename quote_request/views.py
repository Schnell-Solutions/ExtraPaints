import logging

from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages

from affiliates.services import (
    process_referral_on_post,
    record_referral_lead,
    referral_email_line,
    posted_referral_code,
)
from core.forms import QuoteSubmitForm
from core.services.inquiry import confirm_to_customer, notify_sales
from core.services.quote_validation import QuoteItemValidationError, resolve_quote_line
from core.services.rate_limit import rate_limit
from .quote import QuoteList

logger = logging.getLogger(__name__)


@require_POST
def add_to_quote(request):
    quote_list = QuoteList(request)

    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        color_id = request.POST.get('color_id') or None
        size_id = request.POST.get('size_id') or None

        product, color, size = resolve_quote_line(
            product_id=product_id,
            color_id=color_id,
            size_id=size_id,
        )
        quote_list.add(product=product, color=color, size=size, quantity=quantity)

        return JsonResponse({
            'status': 'success',
            'message': 'Item added to quote list.',
            'quote_item_count': len(quote_list)
        })

    except Http404:
        raise
    except QuoteItemValidationError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid quantity.'}, status=400)
    except Exception:
        logger.exception('Error adding item to quote')
        return JsonResponse(
            {'status': 'error', 'message': "Could not add item."},
            status=400)


@rate_limit('quote_submit')
def quote_detail(request):
    quote_list = QuoteList(request)

    if request.method == 'POST':
        form = QuoteSubmitForm(request.POST)
        affiliate, referral_invalid = process_referral_on_post(request)

        if referral_invalid:
            return render(request, 'quote_request/quote_detail.html', {
                'quote_list': quote_list,
                'form': form,
                'referral_invalid': True,
                'referral_value': posted_referral_code(request),
            })

        if not form.is_valid():
            messages.error(request, 'Please check your details and try again.')
            return render(request, 'quote_request/quote_detail.html', {
                'quote_list': quote_list,
                'form': form,
            })

        if len(quote_list) == 0:
            messages.warning(request, 'Add at least one product to your quote list before submitting.')
            return render(request, 'quote_request/quote_detail.html', {
                'quote_list': quote_list,
                'form': form,
            })

        cd = form.cleaned_data
        items_summary = ''
        for item in quote_list:
            details = []
            if item['color']:
                details.append(item['color'].name)
            if item['size']:
                details.append(item['size'].name)
            details_str = f" ({', '.join(details)})" if details else ''
            items_summary += f"- {item['product'].name}{details_str} x {item['quantity']}\n"

        full_quote_request = (
            f"New Quote Request from: {cd['name']} ({cd['email']}, {cd['phone']})\n\n"
            f"Message: {cd.get('message') or '(none)'}\n\n"
            ' ITEMS REQUESTED ------------------------------\n'
            f' {items_summary}'
            f'{referral_email_line(affiliate)}'
        )

        subject = f"New Quote Request — {cd['name']}"
        if notify_sales(
            subject=subject,
            text_body=full_quote_request,
            html_template='quote_request/simple_branded_email.html',
        ):
            record_referral_lead(
                affiliate=affiliate,
                lead_type='quote',
                customer_name=cd['name'],
                customer_email=cd['email'],
                customer_phone=cd['phone'],
                message_excerpt=(cd.get('message') or '')[:500],
                request=request,
            )
            confirm_to_customer(
                email=cd['email'],
                subject='Your quote request was received — ExtraPaints',
                template='home/customer_confirmation.html',
                context={
                    'headline': 'Quote request received',
                    'body': (
                        'Our sales team is reviewing your items and will send a tailored quotation. '
                        'We typically respond within 24 hours on business days.'
                    ),
                    'plain_text': 'We received your quote request and will respond within 24 hours.',
                    'customer_name': cd['name'],
                },
            )
            quote_list.clear()
            request.session['quote_submitted_name'] = cd['name']
            return render(request, 'quote_request/quote_submitted.html', {'customer_name': cd['name']})

        messages.error(request, 'There was an error submitting your quote request. Please try again.')
        return render(request, 'quote_request/quote_detail.html', {
            'quote_list': quote_list,
            'form': form,
        })

    return render(request, 'quote_request/quote_detail.html', {
        'quote_list': quote_list,
        'form': QuoteSubmitForm(),
    })


@require_POST
def remove_from_quote(request):
    quote_list = QuoteList(request)
    item_key = request.POST.get('item_key')

    if item_key:
        quote_list.remove(item_key)

    return JsonResponse({
        'status': 'success',
        'message': 'Item removed',
        'quote_item_count': len(quote_list)
    })


@require_POST
def update_quote(request):
    quote_list = QuoteList(request)
    item_key = request.POST.get('item_key')

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    if item_key:
        quote_list.update(item_key=item_key, quantity=quantity)

    return JsonResponse({
        'status': 'success',
        'message': 'Quantity updated',
        'quote_item_count': len(quote_list),
        'quantity': quantity
    })
