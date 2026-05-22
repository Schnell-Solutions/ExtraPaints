from django.core.management.base import BaseCommand

from colors.models import Color
from core.images import thumbnail_url
from ideas.models import Idea
from portfolio.models import PortfolioProject
from products.models import Product


class Command(BaseCommand):
    help = 'Pre-generate WebP thumbnails for catalog images (400px and 600px widths).'

    def add_arguments(self, parser):
        parser.add_argument('--width', type=int, default=400, help='Thumbnail width in pixels')

    def handle(self, *args, **options):
        width = options['width']
        count = 0
        for product in Product.objects.exclude(main_image='').iterator():
            if product.main_image:
                thumbnail_url(product.main_image, width=width)
                count += 1
        for color in Color.objects.exclude(main_image='').iterator():
            if color.main_image:
                thumbnail_url(color.main_image, width=width)
                count += 1
        for idea in Idea.objects.iterator():
            img = idea.get_display_image
            if img and hasattr(idea, 'main_image') and idea.main_image:
                thumbnail_url(idea.main_image, width=width)
                count += 1
        for project in PortfolioProject.objects.iterator():
            if project.get_display_image and project.main_image:
                thumbnail_url(project.main_image, width=width)
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Warmed {count} image(s) at width={width}'))
