"""Check product/color images on disk and optionally re-link from legacy CSV."""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from colors.models import Color
from core.images import thumbnail_url
from core.legacy_import.utils import media_file_field, pick, read_csv
from products.models import Product


class Command(BaseCommand):
    help = (
        "Report catalog images under MEDIA_ROOT and optionally repair product "
        "main_image paths from data/legacy_export CSV."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir',
            default='data/legacy_export',
            help='Legacy CSV export directory (default: data/legacy_export)',
        )
        parser.add_argument(
            '--repair-from-csv',
            action='store_true',
            help='Re-apply main_image from products_product.csv when the file exists on disk',
        )
        parser.add_argument(
            '--guess-missing',
            action='store_true',
            help='For products with no image, pick a products/main file by name match',
        )
        parser.add_argument(
            '--warm',
            action='store_true',
            help='Warm thumbnails after repair',
        )

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        products_dir = media_root / 'products' / 'main'

        self.stdout.write(f'MEDIA_ROOT = {media_root} (exists={media_root.is_dir()})')
        if products_dir.is_dir():
            count = sum(1 for _ in products_dir.iterdir() if _.is_file())
            self.stdout.write(f'products/main files on disk: {count}')
        else:
            self.stdout.write(self.style.ERROR('products/main/ is missing inside the container/host mount'))

        self._report_products()
        self._report_colors()

        if options['repair_from_csv']:
            self._repair_from_csv(Path(options['dir']))

        if options['guess_missing']:
            self._guess_missing_images(products_dir)

        if options['repair_from_csv'] or options['guess_missing']:
            self.stdout.write('')
            self.stdout.write('--- After repair ---')
            self._report_products()

        if options['warm']:
            from django.core.management import call_command
            call_command('warm_thumbnails')

    def _report_products(self):
        self.stdout.write('')
        self.stdout.write('Products:')
        media_root = Path(settings.MEDIA_ROOT)
        ok = no_path = missing_file = 0

        for product in Product.objects.order_by('name'):
            if not product.main_image:
                self.stdout.write(self.style.WARNING(f'  NO PATH  {product.slug}'))
                no_path += 1
                continue

            rel = product.main_image.name
            full = media_root / rel
            if not full.is_file():
                self.stdout.write(self.style.ERROR(f'  MISSING  {product.slug} -> {rel}'))
                missing_file += 1
                continue

            thumb = thumbnail_url(product.main_image, width=400)
            self.stdout.write(f'  OK       {product.slug} -> {thumb}')
            ok += 1

        total = Product.objects.count()
        self.stdout.write(
            f'  Summary: {ok} ok, {missing_file} path but file missing, '
            f'{no_path} no path, {total} total'
        )

    def _report_colors(self):
        self.stdout.write('')
        self.stdout.write('Colors (main_image only):')
        media_root = Path(settings.MEDIA_ROOT)
        for color in Color.objects.order_by('name')[:5]:
            if not color.main_image:
                continue
            rel = color.main_image.name
            full = media_root / rel
            status = 'OK' if full.is_file() else 'MISSING'
            self.stdout.write(f'  {status} {color.slug} -> {rel}')
        with_img = Color.objects.exclude(main_image='').count()
        self.stdout.write(f'  ({with_img} colors with main_image set)')

    def _repair_from_csv(self, data_dir: Path):
        self.stdout.write('')
        self.stdout.write('Repairing from CSV...')
        updated = skipped = 0

        for row in read_csv(data_dir, 'products_product'):
            slug = pick(row, 'slug').strip()
            if not slug:
                continue
            rel = media_file_field(pick(row, 'main_image'))
            if not rel:
                continue
            product = Product.objects.filter(slug=slug).first()
            if not product:
                skipped += 1
                continue
            if product.main_image.name == rel:
                continue
            product.main_image = rel
            product.save(update_fields=['main_image'])
            updated += 1
            self.stdout.write(f'  linked {slug} -> {rel}')

        self.stdout.write(self.style.SUCCESS(f'  Updated {updated} product(s), skipped {skipped}'))

    def _guess_missing_images(self, products_dir: Path):
        if not products_dir.is_dir():
            self.stdout.write(self.style.ERROR('Cannot guess: products/main/ not found'))
            return

        files = [
            p for p in products_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}
        ]
        linked = 0

        for product in Product.objects.filter(main_image=''):
            rel = self._best_file_match(product.name, files)
            if not rel:
                continue
            product.main_image = rel
            product.save(update_fields=['main_image'])
            linked += 1
            self.stdout.write(f'  guessed {product.slug} -> {rel}')

        self.stdout.write(self.style.SUCCESS(f'  Guessed {linked} product image(s)'))

    @staticmethod
    def _best_file_match(product_name: str, files: list[Path]) -> str:
        import re

        parts = [
            w.lower()
            for w in re.split(r'[\s\-_/]+', product_name)
            if len(w) > 2
        ]
        if not parts:
            return ''

        best_score = 0
        best_rel = ''
        media_root = Path(settings.MEDIA_ROOT)

        for path in files:
            stem = path.stem.lower()
            score = sum(1 for part in parts if part in stem)
            if score > best_score:
                best_score = score
                best_rel = path.relative_to(media_root).as_posix()

        return best_rel if best_score >= 1 else ''
