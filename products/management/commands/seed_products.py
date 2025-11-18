import random
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone

from products.models import Category, SubCategory, Size, Product, SafetyDocument
from colors.models import Color


class Command(BaseCommand):
    help = "Seed the database with realistic categories, subcategories, and products based on new feature flags."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🌱 Starting advanced product catalog seeding..."))

        # --- 1. SIZES ---
        sizes_data = ["250ml", "500ml", "1L", "4L", "20L"]
        sizes = []
        for s in sizes_data:
            size, _ = Size.objects.get_or_create(name=s)
            sizes.append(size)
        self.stdout.write(self.style.SUCCESS(f"✅ Created/Found {len(sizes)} sizes."))

        # --- 2. COLORS ---
        colors = list(Color.objects.filter(is_active=True))
        num_colors = len(colors)
        if not colors:
            self.stdout.write(self.style.WARNING(
                "⚠️ No colors found. Products needing colors will be empty. (Run 'seed_colors' first)"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Found {num_colors} active colors."))

        # --- 3. CATEGORIES & SUBCATEGORIES SETUP ---
        # Format: (Main Category Name, Colors?, Sizes?, [List of Subcategory Names])
        cat_structure = [
            ("Paints", True, True, ["Interior", "Exterior", "Primer", "Specialty"]),
            ("Wood Care", True, True, ["Stains", "Varnishes", "Oils"]),
            ("Automotive", True, True, ["Primers", "Basecoats", "Clearcoats"]),
            ("Industrial", True, True, ["Floor Coatings", "Anti-Corrosive", "Heat Resistant"]),
            ("Solvents & Cleaners", False, True, ["Thinners", "Spirits", "Removers"]),
            ("Tools & Accessories", False, False, ["Brushes", "Rollers", "Trays", "Tape"]),
        ]

        main_cats = {}
        sub_cats = {}

        for main_name, has_colors, has_sizes, subs in cat_structure:
            # Create Main Category
            main_cat, _ = Category.objects.get_or_create(
                name=main_name,
                defaults={
                    "slug": slugify(main_name),
                    "features_colors": has_colors,
                    "features_sizes": has_sizes
                }
            )
            main_cats[main_name] = main_cat

            # Create Subcategories
            for sub_name in subs:
                sub_cat, _ = SubCategory.objects.get_or_create(
                    category=main_cat,
                    name=sub_name,
                    defaults={"slug": slugify(f"{main_name}-{sub_name}")}
                )
                sub_cats[(main_name, sub_name)] = sub_cat

        self.stdout.write(
            self.style.SUCCESS(f"✅ Created/Found {len(main_cats)} main categories and {len(sub_cats)} subcategories."))

        # --- 4. PRODUCTS ---
        # Format: (Name, Description, Main Cat Name, Sub Cat Name (Optional))
        sample_products = [
            # Paints (Colors + Sizes)
            ("Velvet Touch Matte", "Luxurious matte finish for interior walls.", "Paints", "Interior"),
            ("Silk Satin Enamel", "Smooth, washable satin finish for high-traffic areas.", "Paints", "Interior"),
            ("WeatherShield Ultra", "Maximum durability against harsh weather conditions.", "Paints", "Exterior"),
            ("Masonry Guard", "Breathable protection for brick and concrete.", "Paints", "Exterior"),
            ("Multi-Surface Primer", "Ensures perfect adhesion on any surface.", "Paints", "Primer"),

            # Wood Care (Colors + Sizes)
            ("Deep Penetrating Stain", "Enhances natural wood grain with rich color.", "Wood Care", "Stains"),
            ("Polyurethane Varnish", "Tough, clear protection for floors and furniture.", "Wood Care", "Varnishes"),

            # Solvents (Sizes ONLY, NO Colors)
            ("White Spirit", "General purpose thinner and brush cleaner.", "Solvents & Cleaners", "Spirits"),
            ("Paint Thinner Standard", "Effective thinner for oil-based paints.", "Solvents & Cleaners", "Thinners"),
            ("Heavy Duty Remover", "Strips multiple layers of old paint quickly.", "Solvents & Cleaners", "Removers"),

            # Tools (NO Sizes, NO Colors)
            ("Pro-Grade Angled Brush 2\"", "Precise cutting-in and trim work.", "Tools & Accessories", "Brushes"),
            ("Microfiber Roller Sleeve 9\"", "Smooth, lint-free application for all paints.", "Tools & Accessories",
             "Rollers"),
            ("Deep Well Paint Tray", "Sturdy tray holds more paint for fewer refills.", "Tools & Accessories", "Trays"),
            ("Painter's Masking Tape", "Clean lines with no residue, 14-day removal.", "Tools & Accessories", "Tape"),
        ]

        created_count = 0
        for name, desc, main_cat_name, sub_cat_name in sample_products:
            main_cat = main_cats[main_cat_name]
            # Get subcategory if specified, else None
            sub_cat = sub_cats.get((main_cat_name, sub_cat_name))

            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "description": desc,
                    "category": main_cat,
                    "subcategory": sub_cat,
                    "slug": slugify(name),
                    "is_active": True,
                },
            )

            if created:
                created_count += 1

                # 1. Link Sizes (only if category supports it)
                if main_cat.features_sizes:
                    if main_cat_name == "Solvents & Cleaners":
                        product.available_sizes.set([s for s in sizes if s.name in ["1L", "4L", "20L"]])
                    else:
                        product.available_sizes.set(sizes)

                # 2. Link Colors (only if category supports it AND we have colors)
                if main_cat.features_colors and num_colors > 0:
                    # --- FIXED SAMPLING LOGIC ---
                    # Determine a safe range based on how many colors actually exist.
                    # If we have lots of colors (e.g. 50), pick between 15 and 30.
                    # If we have few colors (e.g. 12), pick between 5 and 12.
                    min_sample = min(5, num_colors)
                    max_sample = min(30, num_colors)

                    # Ensure min doesn't exceed max (failsafe)
                    if min_sample > max_sample:
                        min_sample = max_sample

                    sample_count = random.randint(min_sample, max_sample)
                    product.available_colors.set(random.sample(colors, sample_count))

        self.stdout.write(self.style.SUCCESS(
            f"✅ Created {created_count} new products (skipped {len(sample_products) - created_count} existing)."))

        # --- 5. SAFETY DOCUMENTS ---
        if created_count > 0:
            docs_data = [
                ("SDS", "General Safety Data Sheet", "English"),
                ("TDS", "Standard Technical Data Sheet", "English"),
            ]
            for doc_type, title, lang in docs_data:
                doc, _ = SafetyDocument.objects.get_or_create(
                    doc_type=doc_type,
                    title=title,
                    language=lang,
                    defaults={
                        "file": "products/safety_docs/sample.pdf",
                        "version": "v2024.1",
                        "effective_date": timezone.now().date(),
                    }
                )
                # Link to all relevant products (e.g., only paints and solvents need SDS)
                relevant_products = Product.objects.filter(
                    category__name__in=["Paints", "Solvents & Cleaners", "Wood Care", "Automotive", "Industrial"])
                doc.products.add(*relevant_products)

            self.stdout.write(self.style.SUCCESS("📘 Linked safety documents to chemical products."))

        self.stdout.write(self.style.SUCCESS("🎉 Done! Catalog seeding complete."))