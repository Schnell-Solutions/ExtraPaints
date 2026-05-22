from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from affiliates.admin_export import export_affiliates_csv, export_leads_csv
from affiliates.forms import AffiliateAdminForm
from affiliates.models import Affiliate, ReferralLead, ReferralVisit
from affiliates.services import capture_referral_from_query, resolve_active_affiliate
from affiliates.utils import _CODE_ALPHABET, generate_referral_code, is_valid_code_format
from products.models import Category, Product


class ReferralLeadDealFieldsTests(TestCase):
    def test_new_lead_defaults(self):
        aff = Affiliate.objects.create(name='Partner', email='p@example.com', code='PART-X1Y2')
        lead = ReferralLead.objects.create(
            affiliate=aff,
            lead_type='contact',
            customer_name='Client',
            referral_code_used=aff.code,
        )
        self.assertEqual(lead.conversion_status, ReferralLead.ConversionStatus.NEW)
        self.assertEqual(lead.commission_status, ReferralLead.CommissionStatus.NOT_APPLICABLE)


class AdminExportTests(TestCase):
    def setUp(self):
        self.affiliate = Affiliate.objects.create(
            name='Export Partner',
            email='export@example.com',
            code='EXPORT-A1B2',
        )
        ReferralLead.objects.create(
            affiliate=self.affiliate,
            lead_type='quote',
            customer_name='Buyer',
            customer_email='buyer@example.com',
            referral_code_used=self.affiliate.code,
            conversion_status=ReferralLead.ConversionStatus.WON,
            deal_value='150000.00',
        )

    def test_export_affiliates_csv(self):
        response = export_affiliates_csv(Affiliate.objects.filter(pk=self.affiliate.pk))
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        body = response.content.decode('utf-8-sig')
        self.assertIn('EXPORT-A1B2', body)
        self.assertIn('Won deals', body)

    def test_export_leads_csv(self):
        response = export_leads_csv(ReferralLead.objects.all())
        body = response.content.decode('utf-8-sig')
        self.assertIn('Buyer', body)
        self.assertIn('150000', body)


class AffiliateModelTests(TestCase):
    def test_auto_generates_code(self):
        aff = Affiliate.objects.create(name='John Matata', email='john@example.com')
        self.assertTrue(aff.code)
        self.assertIn('-', aff.code)
        self.assertEqual(aff.code, aff.code.upper())

    def test_generate_code_format(self):
        code = generate_referral_code('Sarah Okello')
        self.assertTrue(code.startswith('SARAH-'))
        self.assertEqual(len(code.split('-')[1]), 4)
        self.assertTrue(is_valid_code_format(code))
        suffix = code.split('-')[1]
        self.assertTrue(all(c in _CODE_ALPHABET for c in suffix))

    def test_admin_form_excludes_manual_code(self):
        self.assertNotIn('code', AffiliateAdminForm().fields)


class ReferralAttributionTests(TestCase):
    def setUp(self):
        self.affiliate = Affiliate.objects.create(
            name='Partner One',
            email='partner@example.com',
            code='PARTNER-A1B2',
            is_active=True,
        )
        self.client = Client()

    def test_resolve_active_affiliate(self):
        self.assertEqual(
            resolve_active_affiliate('partner-a1b2').pk,
            self.affiliate.pk,
        )
        self.assertIsNone(resolve_active_affiliate('FAKE-XXXX'))

    def test_ref_query_sets_session(self):
        self.client.get('/?ref=PARTNER-A1B2')
        self.assertEqual(
            self.client.session.get('referral_affiliate_id'),
            self.affiliate.pk,
        )
        self.assertEqual(ReferralVisit.objects.filter(affiliate=self.affiliate).count(), 1)

    def test_invalid_posted_code_does_not_block(self):
        response = self.client.post(
            reverse('contact'),
            {
                'name': 'Test User',
                'email': 'test@example.com',
                'message': 'Hello',
                'referral_code': 'BAD-CODE',
                'website': '',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Referral code not found')
        self.assertEqual(ReferralLead.objects.count(), 0)

    @patch('home.views.notify_sales', return_value=True)
    @patch('home.views.confirm_to_customer', return_value=True)
    def test_continue_without_referral_submits(self, _confirm, _notify):
        response = self.client.post(
            reverse('contact'),
            {
                'name': 'Test User',
                'email': 'test@example.com',
                'message': 'Hello',
                'referral_code': 'BAD-CODE',
                'skip_referral': '1',
                'website': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ReferralLead.objects.count(), 0)

    @patch('quote_request.views.confirm_to_customer', return_value=True)
    @patch('quote_request.views.notify_sales', return_value=True)
    def test_session_attribution_on_quote(self, _notify, _confirm):
        session = self.client.session
        session['referral_affiliate_id'] = self.affiliate.pk
        session.save()
        cat = Category.objects.create(name='Cat', slug='cat')
        prod = Product.objects.create(
            name='Paint',
            slug='paint',
            description='Test paint',
            category=cat,
            is_active=True,
        )
        self.client.post(reverse('quote_add'), {'product_id': prod.id, 'quantity': 1})
        response = self.client.post(
            reverse('quote_detail'),
            {
                'name': 'Buyer',
                'email': 'buyer@example.com',
                'phone': '+254700000000',
                'message': '',
                'website': '',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            ReferralLead.objects.filter(affiliate=self.affiliate, lead_type='quote').count(),
            1,
        )
