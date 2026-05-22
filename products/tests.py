from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from products.models import Category, Product, SavedProducts

User = get_user_model()


class ProductViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Exterior', slug='exterior')
        self.product = Product.objects.create(
            name='Wall Coating',
            slug='wall-coating',
            description='Durable exterior paint',
            category=self.category,
            is_active=True,
        )

    def test_product_list_returns_200(self):
        self.assertEqual(self.client.get(reverse('product_list')).status_code, 200)

    def test_product_detail_returns_200(self):
        self.assertEqual(
            self.client.get(self.product.get_absolute_url()).status_code,
            200,
        )

    def test_product_list_ajax_pagination_meta(self):
        response = self.client.get(
            reverse('product_list'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('products', data)
        self.assertIn('num_pages', data)

    def test_save_toggle_guest(self):
        response = self.client.post(
            reverse('save_product_toggle'),
            {'product_id': self.product.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_saved'])
