from django.db import models

from .utils import generate_referral_code, normalize_referral_code


class Affiliate(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    code = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        blank=True,
        help_text='Auto-generated on save (format: NAME-XXXX).',
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Affiliate / Partner'
        verbose_name_plural = 'Affiliates / Partners'

    def __str__(self):
        return f'{self.name} ({self.code})'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_referral_code(self.name)
        else:
            self.code = normalize_referral_code(self.code)
        super().save(*args, **kwargs)


class ReferralVisit(models.Model):
    """Logged when a visitor lands with ?ref=CODE (validated)."""
    affiliate = models.ForeignKey(
        Affiliate,
        on_delete=models.CASCADE,
        related_name='visits',
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    landing_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Referral visit'
        verbose_name_plural = 'Referral visits'


class ReferralLead(models.Model):
    """Attributed quote, contact, or inquiry submission."""

    class LeadType(models.TextChoices):
        QUOTE = 'quote', 'Quote request'
        CONTACT = 'contact', 'Contact form'
        QUICK_INQUIRY = 'quick_inquiry', 'Quick inquiry'

    class ConversionStatus(models.TextChoices):
        NEW = 'new', 'New lead'
        QUALIFIED = 'qualified', 'Qualified'
        QUOTED = 'quoted', 'Quote sent'
        WON = 'won', 'Won / converted'
        LOST = 'lost', 'Lost'

    class CommissionStatus(models.TextChoices):
        NOT_APPLICABLE = 'na', 'Not applicable'
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        PAID = 'paid', 'Paid'

    affiliate = models.ForeignKey(
        Affiliate,
        on_delete=models.PROTECT,
        related_name='leads',
    )
    lead_type = models.CharField(max_length=20, choices=LeadType.choices)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=30, blank=True)
    message_excerpt = models.CharField(max_length=500, blank=True)
    referral_code_used = models.CharField(max_length=32)
    session_key = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    conversion_status = models.CharField(
        max_length=20,
        choices=ConversionStatus.choices,
        default=ConversionStatus.NEW,
        db_index=True,
        help_text='Internal pipeline status (admin only).',
    )
    deal_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Estimated or closed deal value in KES (optional).',
    )
    commission_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Partner commission amount in KES (optional).',
    )
    commission_status = models.CharField(
        max_length=20,
        choices=CommissionStatus.choices,
        default=CommissionStatus.NOT_APPLICABLE,
        db_index=True,
    )
    conversion_notes = models.TextField(
        blank=True,
        help_text='Internal notes: follow-ups, PO numbers, commission terms, etc.',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Referral lead'
        verbose_name_plural = 'Referral leads'
