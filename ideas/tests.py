from django.test import Client, TestCase
from django.urls import reverse

from ideas.models import Idea, IdeaCategory


class IdeaViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = IdeaCategory.objects.create(name='Living Room', slug='living-room')
        self.idea = Idea.objects.create(
            title='Modern Living',
            slug='modern-living',
            description='Bright open plan',
            category=self.category,
            is_active=True,
        )

    def test_idea_list_returns_200(self):
        self.assertEqual(self.client.get(reverse('idea_list')).status_code, 200)

    def test_idea_detail_returns_200(self):
        self.assertEqual(
            self.client.get(self.idea.get_absolute_url()).status_code,
            200,
        )
