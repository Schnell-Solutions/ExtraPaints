from django.test import Client, TestCase
from django.urls import reverse

from colors.models import Color, ColorCollection
from products.models import Category, Product


class ColorViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.collection = ColorCollection.objects.create(name='Neutrals', slug='neutrals')
        self.color = Color.objects.create(
            name='Soft White',
            code='SW-1',
            hex_code='#f5f5f0',
            collection=self.collection,
            is_active=True,
        )

    def test_color_list_returns_200(self):
        self.assertEqual(self.client.get(reverse('color_list')).status_code, 200)

    def test_color_detail_returns_200(self):
        self.assertEqual(
            self.client.get(self.color.get_absolute_url()).status_code,
            200,
        )

    def test_color_list_ajax_meta(self):
        response = self.client.get(
            reverse('color_list'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('colors', data)
        self.assertIn('page', data)

    def test_ajax_get_color_products_returns_linked_products(self):
        category = Category.objects.create(name='Interior', slug='interior')
        product = Product.objects.create(
            name='Wall Paint',
            slug='wall-paint',
            description='Test',
            category=category,
            is_active=True,
        )
        product.available_colors.add(self.color)

        response = self.client.get(
            reverse('ajax_get_color_products', kwargs={'color_id': self.color.id}),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], product.id)
        self.assertEqual(data[0]['name'], 'Wall Paint')

    def test_ajax_get_color_products_empty_when_not_linked(self):
        response = self.client.get(
            reverse('ajax_get_color_products', kwargs={'color_id': self.color.id}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
