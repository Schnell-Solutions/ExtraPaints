from django.contrib import admin, messages
from django.db.models import Count, Q
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .admin_export import export_affiliates_csv, export_leads_csv, export_visits_csv
from .forms import AffiliateAdminForm
from .models import Affiliate, ReferralLead, ReferralVisit
from .utils import generate_referral_code, regenerate_code_for_affiliate


class ReferralVisitInline(admin.TabularInline):
    model = ReferralVisit
    extra = 0
    readonly_fields = ('session_key', 'ip_address', 'landing_path', 'created_at')
    can_delete = False
    max_num = 20


class ReferralLeadInline(admin.TabularInline):
    model = ReferralLead
    extra = 0
    fields = (
        'created_at', 'lead_type', 'customer_name', 'conversion_status',
        'deal_value', 'commission_status',
    )
    readonly_fields = (
        'created_at', 'lead_type', 'customer_name', 'customer_email',
        'customer_phone', 'message_excerpt', 'referral_code_used',
    )
    can_delete = False
    max_num = 25


@admin.register(Affiliate)
class AffiliateAdmin(admin.ModelAdmin):
    form = AffiliateAdminForm
    list_display = (
        'name', 'code', 'email', 'phone', 'is_active',
        'visit_count', 'lead_count', 'quote_leads', 'won_deals', 'created_at',
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'email', 'code', 'phone')
    inlines = [ReferralVisitInline, ReferralLeadInline]
    actions = ['regenerate_codes', 'export_selected_affiliates']

    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'phone', 'is_active', 'notes'),
        }),
        ('Referral code (automatic)', {
            'fields': ('referral_code_display',),
            'description': (
                'Codes are generated automatically — do not type them manually. '
                'Format: NAME-XXXX (e.g. SARAH-K7M2). Use the list action '
                '"Regenerate referral codes" to issue a new code if needed.'
            ),
        }),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def get_readonly_fields(self, request, obj=None):
        fields = ['referral_code_display', 'created_at', 'updated_at']
        return fields

    def referral_code_display(self, obj):
        if obj and obj.pk and obj.code:
            ref_url = f'{reverse("home")}?ref={obj.code}'
            return format_html(
                '<p style="margin:0 0 0.5rem;">'
                '<strong style="font-size:1.15em;letter-spacing:0.06em;">{}</strong>'
                '</p>'
                '<p style="margin:0 0 0.35rem;color:#444;">Share link: '
                '<a href="{}" target="_blank" rel="noopener"><code>{}</code></a></p>'
                '<p style="margin:0;font-size:12px;color:#666;">'
                'To change this code, select this partner in the list and run '
                '<strong>Regenerate referral codes</strong>.'
                '</p>',
                obj.code,
                ref_url,
                ref_url,
            )
        example = 'NAME-K7M2'
        if obj and obj.name:
            example = generate_referral_code(obj.name)
        return format_html(
            '<p style="margin:0 0 0.5rem;color:#333;">'
            'A unique code will be created when you <strong>Save</strong> '
            '(based on the partner name).'
            '</p>'
            '<p style="margin:0;color:#555;">'
            'Example for this name: <code>{}</code> (final code assigned on save).'
            '</p>',
            example,
        )

    referral_code_display.short_description = 'Referral code'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            self.message_user(
                request,
                f'Partner saved. Referral code: {obj.code} — share as ?ref={obj.code}',
                messages.SUCCESS,
            )

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'dashboard/',
                self.admin_site.admin_view(self.referral_dashboard),
                name='affiliates_affiliate_dashboard',
            ),
        ]
        return custom + urls

    def referral_dashboard(self, request):
        """Lightweight partner metrics overview (staff only)."""
        partners = Affiliate.objects.annotate(
            visit_total=Count('visits', distinct=True),
            lead_total=Count('leads', distinct=True),
            quote_leads=Count('leads', filter=Q(leads__lead_type='quote'), distinct=True),
            won_deals=Count(
                'leads',
                filter=Q(leads__conversion_status=ReferralLead.ConversionStatus.WON),
                distinct=True,
            ),
        ).order_by('-lead_total', 'name')[:50]

        totals = {
            'partners': Affiliate.objects.count(),
            'active_partners': Affiliate.objects.filter(is_active=True).count(),
            'visits': ReferralVisit.objects.count(),
            'leads': ReferralLead.objects.count(),
            'quotes': ReferralLead.objects.filter(
                lead_type=ReferralLead.LeadType.QUOTE,
            ).count(),
            'won': ReferralLead.objects.filter(
                conversion_status=ReferralLead.ConversionStatus.WON,
            ).count(),
        }

        context = {
            **self.admin_site.each_context(request),
            'title': 'Referral partner dashboard',
            'partners': partners,
            'totals': totals,
            'opts': self.model._meta,
        }
        return TemplateResponse(
            request,
            'admin/affiliates/referral_dashboard.html',
            context,
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_referral_dashboard'] = True
        return super().changelist_view(request, extra_context=extra_context)

    def visit_count(self, obj):
        return obj.visits.count()
    visit_count.short_description = 'Visits'

    def lead_count(self, obj):
        return obj.leads.count()
    lead_count.short_description = 'Leads'

    def quote_leads(self, obj):
        return obj.leads.filter(lead_type=ReferralLead.LeadType.QUOTE).count()
    quote_leads.short_description = 'Quotes'

    def won_deals(self, obj):
        return obj.leads.filter(
            conversion_status=ReferralLead.ConversionStatus.WON,
        ).count()
    won_deals.short_description = 'Won'

    @admin.action(description='Regenerate referral codes')
    def regenerate_codes(self, request, queryset):
        updated = []
        for affiliate in queryset:
            updated.append(f'{affiliate.name}: {regenerate_code_for_affiliate(affiliate)}')
        self.message_user(
            request,
            'New codes: ' + '; '.join(updated),
            messages.SUCCESS,
        )

    @admin.action(description='Export selected partners (CSV summary)')
    def export_selected_affiliates(self, request, queryset):
        return export_affiliates_csv(queryset)


@admin.register(ReferralLead)
class ReferralLeadAdmin(admin.ModelAdmin):
    list_display = (
        'created_at', 'lead_type', 'affiliate', 'customer_name',
        'conversion_status', 'deal_value', 'commission_status',
    )
    list_filter = ('lead_type', 'conversion_status', 'commission_status', 'affiliate', 'created_at')
    list_editable = ('conversion_status', 'commission_status')
    search_fields = ('customer_name', 'customer_email', 'affiliate__name', 'affiliate__code')
    actions = ['export_selected_leads']
    date_hierarchy = 'created_at'

    readonly_fields = (
        'affiliate', 'lead_type', 'customer_name', 'customer_email',
        'customer_phone', 'message_excerpt', 'referral_code_used',
        'session_key', 'created_at',
    )

    fieldsets = (
        ('Attribution (read-only)', {
            'fields': (
                'affiliate', 'lead_type', 'referral_code_used', 'created_at',
                'customer_name', 'customer_email', 'customer_phone',
                'message_excerpt', 'session_key',
            ),
        }),
        ('Deal & commission', {
            'fields': (
                'conversion_status', 'deal_value', 'commission_amount',
                'commission_status', 'conversion_notes',
            ),
        }),
    )

    @admin.action(description='Export selected leads (CSV)')
    def export_selected_leads(self, request, queryset):
        return export_leads_csv(queryset)


@admin.register(ReferralVisit)
class ReferralVisitAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'affiliate', 'landing_path', 'ip_address')
    list_filter = ('affiliate', 'created_at')
    search_fields = ('affiliate__name', 'affiliate__code', 'landing_path')
    readonly_fields = ('affiliate', 'session_key', 'ip_address', 'landing_path', 'created_at')
    actions = ['export_selected_visits']
    date_hierarchy = 'created_at'

    @admin.action(description='Export selected visits (CSV)')
    def export_selected_visits(self, request, queryset):
        return export_visits_csv(queryset)
