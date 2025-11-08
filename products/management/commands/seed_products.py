from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from decimal import Decimal
import random

# --- UPDATED IMPORTS ---
# ProductVariant is GONE.
from products.models import Category, Size, Product, SafetyDocument
from colors.models import Color


class Command(BaseCommand):
    help = "Seed the database with demo paint categories, products, sizes, and colors"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🌱 Starting product catalog seeding..."))

        # --- CATEGORIES (Unchanged) ---
        categories_data = [
            ("Interior Paints", "Premium-quality paints for indoor walls and ceilings."),
            ("Exterior Paints", "Durable weather-resistant paints for outdoor surfaces."),
            ("Primers", "Base coatings to ensure smooth and long-lasting finishes."),
            ("Industrial Coatings", "Specialized coatings for factories and heavy-duty applications."),
            ("Wood Finishes", "Protective and decorative finishes for wood surfaces."),
        ]
        categories = []
        for name, desc in categories_data:
            cat, created = Category.objects.get_or_create(
                name=name,
                defaults={"description": desc, "slug": slugify(name)},
            )
            categories.append(cat)
        self.stdout.write(self.style.SUCCESS(f"✅ Created/Found {len(categories)} categories."))

        # --- SIZES (Unchanged) ---
        sizes_data = ["1L", "4L", "20L"]
        sizes = []
        for s in sizes_data:
            size, created = Size.objects.get_or_create(name=s)
            sizes.append(size)
        self.stdout.write(self.style.SUCCESS(f"✅ Created/Found {len(sizes)} sizes."))

        # --- COLORS (Unchanged) ---
        colors = list(Color.objects.all())
        if not colors:
            self.stdout.write(self.style.ERROR("❌ No colors found. Please seed colors first!"))
            return

        # --- PRODUCTS (This section is now updated) ---
        sample_products = [
            ("UltraShield Interior", "High-quality interior emulsion with matte finish.", "Interior Paints"),
            ("WeatherGuard Exterior", "All-weather exterior paint with UV protection.", "Exterior Paints"),
            ("PrimeCoat Base", "Multipurpose primer for smooth adhesion.", "Primers"),
            ("SteelProtect Coating", "Anti-corrosive industrial-grade coating.", "Industrial Coatings"),
            ("WoodGloss Finish", "Glossy finish for wooden furniture and surfaces.", "Wood Finishes"),
        ]

        products = []
        for name, desc, cat_name in sample_products:
            cat = next((c for c in categories if c.name == cat_name), None)
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "description": desc,
                    "category": cat,
                    "slug": slugify(name),
                    "is_active": True,
                },
            )
            products.append(product)

            # --- THIS IS THE NEW LOGIC ---
            # If we just created the product, link its colors and sizes.
            if created:
                # 1. Link all available sizes to this product
                product.available_sizes.set(sizes)

                # 2. Link a random sample of colors (e.g., 10) to this product
                sample_colors = random.sample(colors, min(10, len(colors)))
                product.available_colors.set(sample_colors)

        self.stdout.write(
            self.style.SUCCESS(f"✅ Created/Found {len(products)} products and linked their colors/sizes."))

        # --- VARIANTS (This entire section is GONE) ---
        self.stdout.write(self.style.NOTICE("ℹ️  Variant creation skipped (models updated to catalog)."))

        # --- SAFETY DOCUMENTS (Unchanged) ---
        docs = [
            ("SDS", "Safety Data Sheet Example"),
            ("TDS", "Technical Data Sheet Example"),
            ("GUIDE", "Application Guide Example"),
        ]
        for doc_type, title in docs:
            doc, created = SafetyDocument.objects.get_or_create(
                doc_type=doc_type,
                title=title,
                defaults={
                    "file": "products/safety_docs/sample.pdf",
                    "language": "English",
                    "version": "v1.0",
                    "effective_date": timezone.now().date(),
                },
            )
            # Link all products to this document
            if created:
                doc.products.set(products)
        self.stdout.write(self.style.SUCCESS("📘 Safety documents linked to all products."))

        self.stdout.write(self.style.SUCCESS("✅ Done! Your product catalog is ready to use."))