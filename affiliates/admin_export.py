"""CSV exports for affiliate reporting (admin actions only)."""

import csv
from datetime import datetime

from django.http import HttpResponse
from django.db.models import Count, Q


def _csv_response(filename: str):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')  # UTF-8 BOM for Excel
    return response


def export_affiliates_csv(queryset):
    """Partner summary: visits, leads by type, active status."""
    filename = f'affiliates-summary-{datetime.now():%Y%m%d}.csv'
    response = _csv_response(filename)
    writer = csv.writer(response)

    qs = queryset.annotate(
        visit_total=Count('visits', distinct=True),
        lead_total=Count('leads', distinct=True),
        quote_leads=Count('leads', filter=Q(leads__lead_type='quote'), distinct=True),
        contact_leads=Count('leads', filter=Q(leads__lead_type='contact'), distinct=True),
        inquiry_leads=Count('leads', filter=Q(leads__lead_type='quick_inquiry'), distinct=True),
        won_deals=Count(
            'leads',
            filter=Q(leads__conversion_status='won'),
            distinct=True,
        ),
    )

    writer.writerow([
        'Name', 'Code', 'Email', 'Phone', 'Active',
        'Visits', 'Total leads', 'Quote leads', 'Contact leads', 'Quick inquiries',
        'Won deals', 'Notes', 'Created',
    ])
    for aff in qs:
        writer.writerow([
            aff.name,
            aff.code,
            aff.email,
            aff.phone,
            'Yes' if aff.is_active else 'No',
            aff.visit_total,
            aff.lead_total,
            aff.quote_leads,
            aff.contact_leads,
            aff.inquiry_leads,
            aff.won_deals,
            aff.notes.replace('\n', ' ')[:500] if aff.notes else '',
            aff.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return response


def export_leads_csv(queryset):
    """Detailed referral leads including deal and commission fields."""
    filename = f'referral-leads-{datetime.now():%Y%m%d}.csv'
    response = _csv_response(filename)
    writer = csv.writer(response)

    writer.writerow([
        'Created', 'Partner', 'Partner code', 'Lead type',
        'Customer name', 'Email', 'Phone', 'Message excerpt', 'Code used',
        'Conversion status', 'Deal value (KES)', 'Commission amount (KES)',
        'Commission status', 'Conversion notes',
    ])
    for lead in queryset.select_related('affiliate'):
        writer.writerow([
            lead.created_at.strftime('%Y-%m-%d %H:%M'),
            lead.affiliate.name,
            lead.affiliate.code,
            lead.get_lead_type_display(),
            lead.customer_name,
            lead.customer_email,
            lead.customer_phone,
            lead.message_excerpt,
            lead.referral_code_used,
            lead.get_conversion_status_display(),
            lead.deal_value if lead.deal_value is not None else '',
            lead.commission_amount if lead.commission_amount is not None else '',
            lead.get_commission_status_display(),
            (lead.conversion_notes or '').replace('\n', ' ')[:1000],
        ])
    return response


def export_visits_csv(queryset):
    filename = f'referral-visits-{datetime.now():%Y%m%d}.csv'
    response = _csv_response(filename)
    writer = csv.writer(response)
    writer.writerow(['Created', 'Partner', 'Partner code', 'Landing path', 'IP', 'Session key'])
    for visit in queryset.select_related('affiliate'):
        writer.writerow([
            visit.created_at.strftime('%Y-%m-%d %H:%M'),
            visit.affiliate.name,
            visit.affiliate.code,
            visit.landing_path,
            visit.ip_address or '',
            visit.session_key,
        ])
    return response
