from django.core.management.base import BaseCommand
from django.db import transaction
import datetime
from portfolio.models import PortfolioProject, PortfolioImage
from products.models import Product
from colors.models import Color


class Command(BaseCommand):
    help = 'Populates the database with sample portfolio projects and links them to products/colors.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Populating portfolio projects...')

        # --- 1. Check for dependencies (Products and Colors) ---
        # We need some products and colors to link to.
        products = list(Product.objects.filter(is_active=True)[:4])
        if not products:
            self.stdout.write(self.style.ERROR(
                'No active products found. Please create some Products before running this command.'
            ))
            return

        colors = list(Color.objects.filter(is_active=True)[:5])
        if not colors:
            self.stdout.write(self.style.ERROR(
                'No active colors found. Please create some Colors before running this command.'
            ))
            return

        # --- 2. Clear old data ---
        self.stdout.write('Clearing old portfolio data...')
        PortfolioProject.objects.all().delete()
        PortfolioImage.objects.all().delete()

        # --- 3. Define Sample Data ---
        projects_data = [
            {
                'title': 'Modern Living Room Refresh',
                'project_type': 'residential',
                'location': 'Nairobi, Westlands',
                'client_name': 'Jane & John Doe',
                'description': 'A complete refresh of a family living room, focusing on bright, durable paints. The clients wanted a calm and modern feel, so we used a neutral palette with a bold accent wall.',
                'completion_date': datetime.date(2024, 5, 15),
                'is_featured': True,
                'products_to_link': [products[0]],  # Link the first product
                'colors_to_link': [colors[0], colors[1]]  # Link the first two colors
            },
            {
                'title': '"The Grind" Cafe Fit-Out',
                'project_type': 'commercial',
                'location': 'Mombasa, Nyali',
                'client_name': 'The Grind Coffeehouse',
                'description': 'New commercial fit-out for a high-traffic cafe. Required hard-wearing, scrubbable paint for walls and a high-gloss finish for trim. The theme was "industrial chic".',
                'completion_date': datetime.date(2024, 3, 1),
                'is_featured': True,
                'products_to_link': [products[1], products[2]] if len(products) > 2 else [products[0]],
                'colors_to_link': [colors[2], colors[3]] if len(colors) > 3 else [colors[0]]
            },
            {
                'title': 'Exterior Home Repaint',
                'project_type': 'residential',
                'location': 'Kisumu, Milimani',
                'client_name': 'The Ochieng Family',
                'description': 'Full exterior repaint using our weather-resistant exterior paint. The project involved extensive surface preparation and two top coats for maximum longevity.',
                'completion_date': datetime.date(2024, 4, 22),
                'is_featured': False,
                'products_to_link': [products[3]] if len(products) > 3 else [products[0]],
                'colors_to_link': [colors[4]] if len(colors) > 4 else [colors[1]]
            },
            {
                'title': 'Corporate Office Branding',
                'project_type': 'institutional',
                'location': 'Nairobi, CBD',
                'client_name': 'TechCorp East Africa',
                'description': 'Branding and interior painting for a new 3-floor office. Used low-VOC paints to ensure good air quality for employees returning to the office.',
                'completion_date': datetime.date(2024, 1, 30),
                'is_featured': False,
                'products_to_link': [products[1]],
                'colors_to_link': [colors[0], colors[2]] if len(colors) > 2 else [colors[0]]
            }
        ]

        # --- 4. Create Projects and Images ---
        for data in projects_data:
            # Get products/colors to link
            products_to_link = data.pop('products_to_link', [])
            colors_to_link = data.pop('colors_to_link', [])

            # Create the project
            project = PortfolioProject.objects.create(**data)

            # Link M2M fields
            project.products_used.set(products_to_link)
            project.colors_used.set(colors_to_link)

            # Create gallery images (without actual files, just as placeholders)
            PortfolioImage.objects.create(
                project=project,
                caption=f'Main view of {project.title}',
                alt_text=f'Main view of {project.title}',
                display_order=0
            )
            PortfolioImage.objects.create(
                project=project,
                caption='Detailed shot of paint finish',
                alt_text='Detailed shot of paint finish',
                display_order=1
            )
            PortfolioImage.objects.create(
                project=project,
                caption='Before shot (for comparison)',
                alt_text='Before shot (for comparison)',
                display_order=2
            )

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {len(projects_data)} portfolio projects.'
        ))
