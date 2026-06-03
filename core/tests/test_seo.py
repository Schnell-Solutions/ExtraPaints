import json

from django.test import Client, TestCase
from django.urls import reverse

from core.seo.schema import local_business_json, site_navigation_json, website_search_json
from guides.models import Guide


class SeoInfrastructureTests(TestCase):
    def test_robots_and_sitemap(self):
        client = Client()
        robots = client.get(reverse('robots_txt'))
        self.assertEqual(robots.status_code, 200)
        self.assertIn(b'Sitemap:', robots.content)
        sitemap = client.get('/sitemap.xml')
        self.assertEqual(sitemap.status_code, 200)

    def test_local_business_json_valid(self):
        request = Client().get('/').wsgi_request
        data = json.loads(local_business_json(request))
        self.assertIn('LocalBusiness', data['@type'])
        self.assertEqual(data['address']['addressCountry'], 'KE')

    def test_website_search_action(self):
        request = Client().get('/').wsgi_request
        data = json.loads(website_search_json(request))
        self.assertEqual(data['@type'], 'WebSite')
        self.assertEqual(data['potentialAction']['@type'], 'SearchAction')
        self.assertEqual(data['hasPart']['@id'], data['@id'].replace('#website', '#primary-navigation'))

    def test_site_navigation_json(self):
        request = Client().get('/').wsgi_request
        data = json.loads(site_navigation_json(request))
        self.assertEqual(data['@type'], 'ItemList')
        self.assertGreaterEqual(len(data['itemListElement']), 5)
        first = data['itemListElement'][0]['item']
        self.assertEqual(first['@type'], 'SiteNavigationElement')
        self.assertIn('/products/', first['url'])

    def test_home_includes_sitelink_navigation_schema(self):
        response = Client().get(reverse('home'))
        self.assertContains(response, 'SiteNavigationElement', status_code=200)
        self.assertContains(response, '#primary-navigation', status_code=200)

    def test_login_page_noindex(self):
        response = Client().get(reverse('login'))
        self.assertContains(response, 'noindex', status_code=200)

    def test_home_page_indexable(self):
        response = Client().get(reverse('home'))
        self.assertContains(response, 'index, follow', status_code=200)
        self.assertContains(response, 'application/ld+json', status_code=200)

    def test_home_products_api(self):
        from products.models import Category, Product

        cat = Category.objects.create(name='Test Cat', slug='test-cat')
        Product.objects.create(
            name='API Paint',
            slug='api-paint',
            description='x',
            category=cat,
            is_active=True,
        )
        response = Client().get(reverse('home_products_api'), {'category': 'Test Cat'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['products']), 1)

    def test_guide_list_and_detail(self):
        Guide.objects.create(
            title='Test Guide',
            slug='test-guide',
            excerpt='Test excerpt for SEO.',
            body='<p>Body</p>',
            is_published=True,
        )
        client = Client()
        self.assertEqual(client.get(reverse('guide_list')).status_code, 200)
        detail = client.get(reverse('guide_detail', args=['test-guide']))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, 'BreadcrumbList', status_code=200)
