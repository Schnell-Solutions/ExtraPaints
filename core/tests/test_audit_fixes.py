import json

from django.contrib.auth import authenticate, get_user_model
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from core.seo.helpers import schema_json_ld_blocks
from products.models import Category, Product, SavedProducts

User = get_user_model()


class ProductDetailAuditTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Interior', slug='interior')
        self.product = Product.objects.create(
            name='Audit Paint',
            slug='audit-paint',
            description='<p>Test product</p>',
            category=self.category,
            is_active=True,
        )

    def test_product_detail_returns_200(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Audit Paint')

    def test_product_detail_has_valid_json_ld_blocks(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        scripts = response.content.decode().count('application/ld+json')
        self.assertGreaterEqual(scripts, 3)

    def test_schema_blocks_helper_filters_empty(self):
        blocks = schema_json_ld_blocks('{"a":1}', '', '{"b":2}')
        self.assertEqual(len(blocks), 2)
        json.loads(blocks[0])
        json.loads(blocks[1])


class AuthAuditTests(TestCase):
    def _verified_user(self, *, username='jane', email='jane@example.com', password='SecurePass123!'):
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_email_verified = True
        user.is_active = True
        user.save(update_fields=['is_email_verified', 'is_active'])
        return user

    def test_authenticate_with_email(self):
        from accounts.backends import EmailOrUsernameBackend

        self._verified_user()
        request = RequestFactory().get('/')
        backend = EmailOrUsernameBackend()
        user = backend.authenticate(
            request,
            username='jane@example.com',
            password='SecurePass123!',
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'jane@example.com')

    def test_merge_guest_saves_service(self):
        from core.services.guest_merge import merge_guest_saves_into_user
        from django.test import RequestFactory

        cat = Category.objects.create(name='M', slug='m-cat')
        product = Product.objects.create(
            name='P', slug='p', description='x', category=cat, is_active=True
        )
        user = self._verified_user(username='merger2', email='merger2@example.com')
        request = RequestFactory().get('/')
        request.session = Client().session
        request.session['guest_saved_products'] = [product.id]
        request.session.save()
        merge_guest_saves_into_user(request, user)
        self.assertTrue(SavedProducts.objects.filter(user=user, product=product).exists())
