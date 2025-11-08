import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from ideas.models import Idea, Category, Tag, IdeaImage, SavedIdea
from colors.models import Color  # We need this for the M2M link


class Command(BaseCommand):
    help = 'Populates the database with sample ideas, tags, and categories.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Checking for existing data...')

        # --- 1. Get or Create a User ---
        User = get_user_model()
        user, user_created = User.objects.get_or_create(
            username='ideatester',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Idea',
                'last_name': 'Tester'
            }
        )
        if user_created:
            user.set_password('password123')
            user.save()
            self.stdout.write(f'Created user: {user.username}')

        # --- 2. Get or Create Categories ---
        cat1, _ = Category.objects.get_or_create(name='Living Rooms', defaults={'slug': 'living-rooms'})
        cat2, _ = Category.objects.get_or_create(name='Exteriors', defaults={'slug': 'exteriors'})
        cat3, _ = Category.objects.get_or_create(name='Bedrooms', defaults={'slug': 'bedrooms'})
        cat4, _ = Category.objects.get_or_create(name='Kitchens', defaults={'slug': 'kitchens'})

        # --- 3. Get or Create Tags ---
        tag1, _ = Tag.objects.get_or_create(name='Minimalist', defaults={'slug': 'minimalist'})
        tag2, _ = Tag.objects.get_or_create(name='Cozy', defaults={'slug': 'cozy'})
        tag3, _ = Tag.objects.get_or_create(name='Modern', defaults={'slug': 'modern'})
        tag4, _ = Tag.objects.get_or_create(name='Bold', defaults={'slug': 'bold'})
        tag5, _ = Tag.objects.get_or_create(name='Neutral', defaults={'slug': 'neutral'})

        # --- 4. Get or Create Colors ---
        color1, _ = Color.objects.get_or_create(name='Ocean Breeze', defaults={'code': 'OB-202', 'hex_code': '#A0D6E8'})
        color2, _ = Color.objects.get_or_create(name='Pebble Gray', defaults={'code': 'PG-110', 'hex_code': '#BDBDBD'})
        color3, _ = Color.objects.get_or_create(name='Warm Sand', defaults={'code': 'WS-301', 'hex_code': '#D2B48C'})
        color4, _ = Color.objects.get_or_create(name='Forest Green', defaults={'code': 'FG-450', 'hex_code': '#228B22'})
        color5, _ = Color.objects.get_or_create(name='Pure White', defaults={'code': 'PW-100', 'hex_code': '#FFFFFF'})

        self.stdout.write('Creating 4 sample ideas...')

        # --- 5. Create Ideas ---

        # Idea 1
        idea1, _ = Idea.objects.get_or_create(
            title='Cozy Minimalist Living Room',
            defaults={
                'description': 'A calm and relaxing living space that combines the warmth of cozy textiles with the clean lines of minimalist design. Perfect for unwinding.',
                'category': cat1,
                'created_by': user,
                'mood': 'Calm, Cozy',
                'is_featured': True,
                'is_active': True
            }
        )
        idea1.tags.set([tag1, tag2, tag5])
        idea1.paint_colors.set([color2, color3, color5])

        # Idea 2
        idea2, _ = Idea.objects.get_or_create(
            title='Modern Bedroom Retreat',
            defaults={
                'description': 'A sleek, modern bedroom using cool tones to create a restful environment. Features bold lighting and simple furniture.',
                'category': cat3,
                'created_by': user,
                'mood': 'Restful, Sleek',
                'is_active': True
            }
        )
        idea2.tags.set([tag3, tag1])
        idea2.paint_colors.set([color1, color2, color5])

        # Idea 3
        idea3, _ = Idea.objects.get_or_create(
            title='Bold Exterior Statement',
            defaults={
                'description': 'Make an impact with a dark, moody exterior. This look uses a deep green to contrast with natural wood elements.',
                'category': cat2,
                'created_by': user,
                'mood': 'Confident, Dramatic',
                'is_featured': True,
                'is_active': True
            }
        )
        idea3.tags.set([tag4, tag3])
        idea3.paint_colors.set([color4, color2])

        # Idea 4
        idea4, _ = Idea.objects.get_or_create(
            title='Warm and Inviting Kitchen',
            defaults={
                'description': 'A neutral kitchen that feels anything but boring. Warm sand-colored cabinets create a timeless and inviting atmosphere for cooking and gathering.',
                'category': cat4,
                'created_by': user,
                'mood': 'Inviting, Warm',
                'is_active': True
            }
        )
        idea4.tags.set([tag2, tag5])
        idea4.paint_colors.set([color3, color5])

        # --- 6. Create Gallery Images (Optional) ---
        # Note: These will not have image files, but the records will exist.
        # Your .get_display_image property will use the placeholder.
        IdeaImage.objects.get_or_create(idea=idea1, display_order=0,
                                        defaults={'caption': 'Main view of the cozy living room.'})
        IdeaImage.objects.get_or_create(idea=idea1, display_order=1, defaults={'caption': 'Reading nook detail.'})
        IdeaImage.objects.get_or_create(idea=idea3, display_order=0, defaults={'caption': 'Front door contrast.'})

        # --- 7. Create Saved Ideas for the test user ---
        SavedIdea.objects.get_or_create(user=user, idea=idea1)
        SavedIdea.objects.get_or_create(user=user, idea=idea3)

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with 4 ideas and related data.'))
