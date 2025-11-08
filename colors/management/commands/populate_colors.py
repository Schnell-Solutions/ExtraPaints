from django.core.management.base import BaseCommand
from colors.models import Color, ColorCollection, Finish, Surface, RoomType, ColorImage
from django.utils.text import slugify
from decimal import Decimal

class Command(BaseCommand):
    help = "Populate database with demo color data"

    def handle(self, *args, **options):
        # --- Collections ---
        collections = [
            {"name": "Designer Series", "description": "Premium, elegant tones for modern interiors."},
            {"name": "Coastal Collection", "description": "Soft blues and whites inspired by coastal living."},
        ]
        collection_objs = []
        for data in collections:
            obj, _ = ColorCollection.objects.get_or_create(
                name=data["name"],
                defaults={"description": data["description"], "slug": slugify(data["name"])}
            )
            collection_objs.append(obj)

        # --- Finishes ---
        finishes = ["Matte", "Satin", "Gloss"]
        finish_objs = [Finish.objects.get_or_create(name=f)[0] for f in finishes]

        # --- Surfaces ---
        surfaces = ["Walls", "Wood", "Metal"]
        surface_objs = [Surface.objects.get_or_create(name=s)[0] for s in surfaces]

        # --- Room Types ---
        rooms = ["Living Room", "Bedroom", "Office", "Kitchen", "Bathroom"]
        room_objs = [RoomType.objects.get_or_create(name=r)[0] for r in rooms]

        # --- Color Images ---
        image_objs = []
        for i in range(1, 4):
            img, _ = ColorImage.objects.get_or_create(
                caption=f"Sample Inspiration {i}",
                defaults={"image": f"colors/inspirations/sample{i}.jpg"}
            )
            image_objs.append(img)

        # --- Colors (Expanded List) ---
        colors_data = [
            # Original Colors
            {
                "name": "Ocean Breeze",
                "code": "OB-202",
                "hex_code": "#5DADE2",
                "rgb_value": "93,173,226",
                "undertone": "cool",
                "lrv": Decimal("58.2"),
                "opacity_strength": "medium",
                "description": "A calm, refreshing blue inspired by seaside mornings.",
                "collection": collection_objs[1], # Coastal Collection
            },
            {
                "name": "Golden Glow",
                "code": "GG-305",
                "hex_code": "#F7DC6F",
                "rgb_value": "247,220,111",
                "undertone": "warm",
                "lrv": Decimal("72.4"),
                "opacity_strength": "strong",
                "description": "A bright golden hue that adds warmth and cheer to any room.",
                "collection": collection_objs[0], # Designer Series
            },
            {
                "name": "Pebble Gray",
                "code": "PG-110",
                "hex_code": "#B2BABB",
                "rgb_value": "178,186,187",
                "undertone": "neutral",
                "lrv": Decimal("46.9"),
                "opacity_strength": "medium",
                "description": "A versatile neutral tone perfect for minimalist interiors.",
                "collection": collection_objs[0], # Designer Series
            },
            # New Colors Added Below
            {
                "name": "Crimson Red",
                "code": "CR-410",
                "hex_code": "#C0392B",
                "rgb_value": "192,57,43",
                "undertone": "warm",
                "lrv": Decimal("15.1"),
                "opacity_strength": "strong",
                "description": "A bold and passionate red for creating a statement accent wall.",
                "collection": collection_objs[0], # Designer Series
            },
            {
                "name": "Forest Green",
                "code": "FG-501",
                "hex_code": "#229954",
                "rgb_value": "34,153,84",
                "undertone": "cool",
                "lrv": Decimal("25.6"),
                "opacity_strength": "strong",
                "description": "A deep, rich green that brings the serenity of nature indoors.",
                "collection": collection_objs[0], # Designer Series
            },
            {
                "name": "Cloud White",
                "code": "CW-001",
                "hex_code": "#FDFEFE",
                "rgb_value": "253,254,254",
                "undertone": "neutral",
                "lrv": Decimal("92.0"),
                "opacity_strength": "medium",
                "description": "A soft, clean white that provides a bright and airy feel.",
                "collection": collection_objs[1], # Coastal Collection
            },
            {
                "name": "Charcoal Slate",
                "code": "CS-808",
                "hex_code": "#34495E",
                "rgb_value": "52,73,94",
                "undertone": "cool",
                "lrv": Decimal("8.5"),
                "opacity_strength": "strong",
                "description": "A sophisticated dark gray for modern, dramatic spaces.",
                "collection": collection_objs[0], # Designer Series
            },
            {
                "name": "Sandy Beige",
                "code": "SB-150",
                "hex_code": "#F5CBA7",
                "rgb_value": "245,203,167",
                "undertone": "warm",
                "lrv": Decimal("65.3"),
                "opacity_strength": "medium",
                "description": "A warm, inviting beige reminiscent of a sunny beach.",
                "collection": collection_objs[1], # Coastal Collection
            },
            {
                "name": "Minty Fresh",
                "code": "MF-220",
                "hex_code": "#A3E4D7",
                "rgb_value": "163,228,215",
                "undertone": "cool",
                "lrv": Decimal("75.1"),
                "opacity_strength": "light",
                "description": "A light and airy mint green, perfect for bathrooms and kitchens.",
                "collection": collection_objs[0], # Designer Series
            },
            {
                "name": "Deep Navy",
                "code": "DN-740",
                "hex_code": "#283747",
                "rgb_value": "40,55,71",
                "undertone": "cool",
                "lrv": Decimal("6.2"),
                "opacity_strength": "strong",
                "description": "A classic, deep navy blue for a timeless and elegant look.",
                "collection": collection_objs[1], # Coastal Collection
            },
        ]

        for color_data in colors_data:
            color, created = Color.objects.get_or_create(
                name=color_data["name"],
                defaults=color_data
            )
            if created:
                color.available_finishes.set(finish_objs)
                color.recommended_surfaces.set(surface_objs)
                color.recommended_rooms.set(room_objs)
                color.inspiration_images.set(image_objs)
                color.coverage_per_liter = Decimal("12.5")
                color.drying_time_hours = Decimal("2.5")
                color.voc_level = "Low"
                color.save()

        self.stdout.write(self.style.SUCCESS("✅ Demo color data successfully populated!"))