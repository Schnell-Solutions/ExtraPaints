from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from colors.models import Color
from products.models import Category, Product, Size

User = get_user_model()


class RobotsAndSitemapTests(TestCase):
    def test_robots_txt_returns_200(self):
        response = Client().get(reverse('robots_txt'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sitemap:', response.content)
        self.assertIn(b'User-agent:', response.content)

    def test_sitemap_xml_returns_200(self):
        response = Client().get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'urlset', status_code=200)

    def test_whatsapp_float_on_public_pages(self):
        for url_name in ('home', 'about', 'product_list', 'color_list'):
            response = Client().get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'id="ep-whatsapp-float"')
            self.assertContains(response, 'class="ep-whatsapp-float"')
            self.assertContains(response, 'wa.me/')


class QuoteFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Interior', slug='interior')
        self.active_product = Product.objects.create(
            name='Active Paint',
            slug='active-paint',
            description='Test',
            category=self.category,
            is_active=True,
        )
        self.inactive_product = Product.objects.create(
            name='Inactive Paint',
            slug='inactive-paint',
            description='Test',
            category=self.category,
            is_active=False,
        )

    def test_add_active_product_to_quote(self):
        response = self.client.post(
            reverse('quote_add'),
            {'product_id': self.active_product.id, 'quantity': 2},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['quote_item_count'], 1)

    def test_reject_inactive_product_for_quote(self):
        response = self.client.post(
            reverse('quote_add'),
            {'product_id': self.inactive_product.id, 'quantity': 1},
        )
        self.assertEqual(response.status_code, 404)

    def test_reject_color_not_on_product(self):
        listed = Color.objects.create(
            name='Listed Blue',
            code='LB-1',
            hex_code='#0055aa',
            is_active=True,
        )
        other = Color.objects.create(
            name='Other Blue',
            code='OB-2',
            hex_code='#0066bb',
            is_active=True,
        )
        self.active_product.available_colors.add(listed)
        response = self.client.post(
            reverse('quote_add'),
            {
                'product_id': self.active_product.id,
                'color_id': other.id,
                'quantity': 1,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('not available', response.json()['message'].lower())

    @patch('quote_request.views.confirm_to_customer', return_value=True)
    @patch('quote_request.views.notify_sales', return_value=True)
    def test_quote_submit_sends_email_and_clears_session(self, mock_sales, mock_confirm):
        self.client.post(
            reverse('quote_add'),
            {'product_id': self.active_product.id, 'quantity': 1},
        )
        response = self.client.post(
            reverse('quote_detail'),
            {
                'name': 'Jane Doe',
                'email': 'jane@example.com',
                'phone': '0700000000',
                'message': 'Need a quote',
                'website': '',
            },
        )
        self.assertEqual(response.status_code, 200)
        mock_sales.assert_called_once()
        mock_confirm.assert_called_once()
        self.assertTemplateUsed(response, 'quote_request/quote_submitted.html')


class SaveToggleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass12345')
        self.client = Client()
        self.category = Category.objects.create(name='Exterior', slug='exterior')
        self.active_product = Product.objects.create(
            name='Wall Paint',
            slug='wall-paint',
            description='Test',
            category=self.category,
            is_active=True,
        )
        self.inactive_product = Product.objects.create(
            name='Old Stock',
            slug='old-stock',
            description='Test',
            category=self.category,
            is_active=False,
        )

    def test_save_product_toggle_authenticated(self):
        self.client.login(username='tester', password='pass12345')
        response = self.client.post(
            reverse('save_product_toggle'),
            {'product_id': self.active_product.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_saved'])

    def test_save_product_toggle_guest_session(self):
        client = Client()
        response = client.post(
            reverse('save_product_toggle'),
            {'product_id': self.active_product.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_saved'])
        session = client.session
        self.assertIn(self.active_product.id, session.get('guest_saved_products', []))

    def test_save_product_toggle_rejects_inactive(self):
        self.client.login(username='tester', password='pass12345')
        response = self.client.post(
            reverse('save_product_toggle'),
            {'product_id': self.inactive_product.id},
        )
        self.assertEqual(response.status_code, 404)


class ContactFormTests(TestCase):
    @patch('home.views.confirm_to_customer', return_value=True)
    @patch('home.views.notify_sales', return_value=True)
    def test_contact_post_success(self, mock_sales, mock_confirm):
        response = Client().post(
            reverse('contact'),
            {
                'name': 'John',
                'email': 'john@example.com',
                'phone': '+254700000000',
                'message': 'Hello',
                'website': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        mock_sales.assert_called_once()
        mock_confirm.assert_called_once()

    def test_contact_honeypot_rejected(self):
        response = Client().post(
            reverse('contact'),
            {
                'name': 'Bot',
                'email': 'bot@evil.com',
                'message': 'spam',
                'website': 'http://spam.test',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'correct the errors', status_code=200)
