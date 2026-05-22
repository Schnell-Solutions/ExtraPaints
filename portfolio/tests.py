from django.test import Client, TestCase
from django.urls import reverse

from portfolio.models import PortfolioProject


class PortfolioViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = PortfolioProject.objects.create(
            title='Office Block',
            slug='office-block',
            description='Commercial repaint',
            is_active=True,
        )

    def test_portfolio_list_returns_200(self):
        self.assertEqual(self.client.get(reverse('portfolio_list')).status_code, 200)

    def test_portfolio_detail_returns_200(self):
        self.assertEqual(
            self.client.get(self.project.get_absolute_url()).status_code,
            200,
        )
