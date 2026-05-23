"""
Import legacy SQLite data from CSV exports into the NEW schema.

Old DB tables that do not exist anymore (AuthOTP, AccountDeletionRequest, affiliates…)
are skipped automatically. New model fields get Django defaults.

Workflow:
  1. python3 scripts/export_sqlite_to_csv.py /path/to/db.sqlite3 -o data/legacy_export
  2. (optional) Edit CSVs in Excel
  3. scp -r data/legacy_export root@SERVER:/home/james/extrapaints/data/
  4. docker compose exec web python manage.py import_legacy_csv --dir data/legacy_export --dry-run
  5. docker compose exec web python manage.py import_legacy_csv --dir data/legacy_export --step all
"""
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from colors.models import Color, ColorCollection, RoomType
from core.legacy_import.utils import (
    as_bool,
    as_int,
    media_file_field,
    pick,
    read_csv,
    slugify_fallback,
)
from ideas.models import Idea, IdeaCategory, IdeaImage
from portfolio.models import PortfolioImage, PortfolioProject
from products.models import (
    ApplicationMethod,
    Category,
    Finish,
    Product,
    Size,
    SubCategory,
    Surface,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Import legacy catalog CSVs (safe for schema changes; use --dry-run first)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir",
            default="data/legacy_export",
            help="Directory with table CSV files from export_sqlite_to_csv.py",
        )
        parser.add_argument(
            "--step",
            choices=(
                "all",
                "lookups",
                "categories",
                "colors",
                "products",
                "ideas",
                "portfolio",
                "newsletter",
                "users",
            ),
            default="all",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without saving.",
        )

    def handle(self, *args, **options):
        data_dir = Path(options["dir"])
        if not data_dir.is_dir():
            raise CommandError(f"Not found: {data_dir}")

        dry = options["dry_run"]
        if dry:
            self.stdout.write(self.style.WARNING("DRY RUN — no data will be saved.\n"))

        steps = self._resolve_steps(options["step"])
        maps = {
            "category": {},
            "subcategory": {},
            "finish": {},
            "surface": {},
            "size": {},
            "tool": {},
            "color": {},
            "product": {},
            "idea_category": {},
            "idea": {},
            "portfolio": {},
        }

        with transaction.atomic():
            for step in steps:
                getattr(self, f"_step_{step}")(data_dir, maps, dry)
            if dry:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS("\nImport finished."))

    def _resolve_steps(self, step: str) -> list[str]:
        if step == "all":
            return [
                "lookups",
                "categories",
                "colors",
                "products",
                "ideas",
                "portfolio",
                "newsletter",
            ]
        if step == "users":
            return ["users"]
        return [step]

    def _step_lookups(self, data_dir: Path, maps: dict, dry: bool) -> None:
        self.stdout.write("--- Lookups (finish, surface, size, tools) ---")
        for table, model, key in (
            ("products_finish", Finish, "finish"),
            ("products_surface", Surface, "surface"),
            ("products_size", Size, "size"),
            ("products_applicationmethod", ApplicationMethod, "tool"),
        ):
            n = 0
            for row in read_csv(data_dir, table):
                name = pick(row, "name").strip()
                if not name:
                    continue
                n += 1
                if dry:
                    continue
                obj, _ = model.objects.get_or_create(name=name)
                if row.get("id"):
                    maps[key][row["id"]] = obj
            self.stdout.write(f"  {table}: {n}")

        for row in read_csv(data_dir, "colors_roomtype"):
            name = pick(row, "name").strip()
            if not name or dry:
                continue
            RoomType.objects.get_or_create(name=name)

    def _step_categories(self, data_dir: Path, maps: dict, dry: bool) -> None:
        self.stdout.write("--- Categories ---")
        n = 0
        for row in read_csv(data_dir, "products_category"):
            name = pick(row, "name").strip()
            if not name:
                continue
            n += 1
            if dry:
                continue
            slug = pick(row, "slug").strip() or slugify_fallback(name)
            obj, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "features_colors": as_bool(pick(row, "features_colors"), True),
                    "features_sizes": as_bool(pick(row, "features_sizes"), True),
                },
            )
            if row.get("id"):
                maps["category"][row["id"]] = obj

        for row in read_csv(data_dir, "products_subcategory"):
            name = pick(row, "name").strip()
            cat = maps["category"].get(row.get("category_id"))
            if not name or (not dry and not cat):
                continue
            n += 1
            if dry:
                continue
            slug = pick(row, "slug").strip() or slugify_fallback(f"{cat.name}-{name}")
            obj, _ = SubCategory.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "category": cat},
            )
            if row.get("id"):
                maps["subcategory"][row["id"]] = obj
        self.stdout.write(f"  categories/subcategories: {n}")

    def _step_colors(self, data_dir: Path, maps: dict, dry: bool) -> None:
        self.stdout.write("--- Colors ---")
        collections = {}
        for row in read_csv(data_dir, "colors_colorcollection"):
            name = pick(row, "name").strip()
            if not name or dry:
                continue
            slug = pick(row, "slug").strip() or slugify_fallback(name, 120)
            coll, _ = ColorCollection.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "description": pick(row, "description", default="")},
            )
            if row.get("id"):
                collections[row["id"]] = coll

        n = 0
        for row in read_csv(data_dir, "colors_color"):
            name = pick(row, "name").strip()
            code = pick(row, "code").strip() or name
            if not name:
                continue
            n += 1
            if dry:
                continue
            coll = collections.get(row.get("collection_id"))
            img = media_file_field(pick(row, "main_image"))
            defaults = {
                "name": name,
                "hex_code": pick(row, "hex_code") or None,
                "rgb_value": pick(row, "rgb_value") or None,
                "cmyk_value": pick(row, "cmyk_value") or None,
                "undertone": pick(row, "undertone") or None,
                "lrv": pick(row, "lrv") or None,
                "description": pick(row, "description") or None,
                "is_active": as_bool(pick(row, "is_active"), True),
                "collection": coll,
            }
            if img:
                defaults["main_image"] = img
            slug = pick(row, "slug").strip() or slugify_fallback(f"{name}-{code}", 150)
            obj, _ = Color.objects.update_or_create(code=code, defaults={**defaults, "slug": slug})
            if row.get("id"):
                maps["color"][row["id"]] = obj

        if not dry:
            linked = 0
            for row in read_csv(data_dir, "colors_color_recommended_rooms"):
                color = maps["color"].get(row.get("color_id"))
                if not color:
                    continue
                room = RoomType.objects.filter(pk=row.get("roomtype_id")).first()
                if room:
                    color.recommended_rooms.add(room)
                    linked += 1
            if linked:
                self.stdout.write(f"  colors_color_recommended_rooms: {linked} links")

        self.stdout.write(f"  colors: {n}")

    def _step_products(self, data_dir: Path, maps: dict, dry: bool) -> None:
        self.stdout.write("--- Products ---")
        if not maps["category"] and not dry:
            self._step_categories(data_dir, maps, dry=False)

        n = 0
        for row in read_csv(data_dir, "products_product"):
            name = pick(row, "name").strip()
            if not name:
                continue
            cat = maps["category"].get(row.get("category_id"))
            if not dry and not cat:
                self.stdout.write(self.style.WARNING(f"  skip (no category): {name}"))
                continue
            n += 1
            if dry:
                continue

            sub = maps["subcategory"].get(row.get("subcategory_id"))
            finish = maps["finish"].get(row.get("finish_id"))
            slug = pick(row, "slug").strip() or slugify_fallback(name)
            img = media_file_field(pick(row, "main_image"))
            defaults = {
                "name": name,
                "description": pick(row, "description", default=""),
                "category": cat,
                "subcategory": sub,
                "finish": finish,
                "is_active": as_bool(pick(row, "is_active"), True),
                "drying_time": pick(row, "drying_time") or "",
                "coverage_rate": pick(row, "coverage_rate") or None,
                "coats_required": as_int(pick(row, "coats_required")),
            }
            if img:
                defaults["main_image"] = img
            obj, _ = Product.objects.update_or_create(slug=slug, defaults=defaults)
            if row.get("id"):
                maps["product"][row["id"]] = obj

        if not dry:
            self._import_m2m(
                data_dir,
                "products_product_available_colors",
                maps["product"],
                maps["color"],
                "color_id",
                "available_colors",
            )
            self._import_m2m(
                data_dir,
                "products_product_available_sizes",
                maps["product"],
                maps["size"],
                "size_id",
                "available_sizes",
            )
            self._import_m2m(
                data_dir,
                "products_product_suitable_surfaces",
                maps["product"],
                maps["surface"],
                "surface_id",
                "suitable_surfaces",
            )
            self._import_m2m(
                data_dir,
                "products_product_tools_needed",
                maps["product"],
                maps["tool"],
                "applicationmethod_id",
                "tools_needed",
            )
        self.stdout.write(f"  products: {n}")

    def _import_m2m(self, data_dir, table, left_map, right_map, right_id_col, m2m_field):
        rows = read_csv(data_dir, table)
        if not rows:
            return
        linked = 0
        for row in rows:
            left = left_map.get(row.get("product_id"))
            right = right_map.get(row.get(right_id_col))
            if not left or not right:
                continue
            getattr(left, m2m_field).add(right)
            linked += 1
        if linked:
            self.stdout.write(f"  {table}: {linked} links")

    def _step_ideas(self, data_dir: Path, maps: dict, dry: bool) -> None:
        self.stdout.write("--- Ideas ---")
        for row in read_csv(data_dir, "ideas_ideacategory") or read_csv(data_dir, "ideas_category"):
            name = pick(row, "name").strip()
            if not name or dry:
                continue
            slug = pick(row, "slug").strip() or slugify_fallback(name)
            obj, _ = IdeaCategory.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "description": pick(row, "description", default="")},
            )
            if row.get("id"):
                maps["idea_category"][row["id"]] = obj

        n = 0
        for row in read_csv(data_dir, "ideas_idea"):
            title = pick(row, "title").strip()
            if not title:
                continue
            n += 1
            if dry:
                continue
            cat = maps["idea_category"].get(row.get("category_id"))
            slug = pick(row, "slug").strip() or slugify_fallback(title, 255)
            img = media_file_field(pick(row, "main_image"))
            defaults = {
                "title": title,
                "description": pick(row, "description", default=""),
                "category": cat,
                "is_featured": as_bool(pick(row, "is_featured")),
                "is_active": as_bool(pick(row, "is_active"), True),
                "mood": pick(row, "mood") or None,
            }
            if img:
                defaults["main_image"] = img
            obj, _ = Idea.objects.update_or_create(slug=slug, defaults=defaults)
            if row.get("id"):
                maps["idea"][row["id"]] = obj

        g = 0
        for row in read_csv(data_dir, "ideas_ideaimage"):
            if dry:
                g += 1
                continue
            idea = maps["idea"].get(row.get("idea_id"))
            img = media_file_field(pick(row, "image"))
            if not idea or not img:
                continue
            IdeaImage.objects.get_or_create(
                idea=idea,
                image=img,
                defaults={
                    "caption": pick(row, "caption", default=""),
                    "display_order": as_int(pick(row, "display_order"), 0),
                },
            )
            g += 1
        self.stdout.write(f"  ideas: {n}, gallery: {g}")

    def _step_portfolio(self, data_dir: Path, maps: dict, dry: bool) -> None:
        self.stdout.write("--- Portfolio ---")
        n = 0
        for row in read_csv(data_dir, "portfolio_portfolioproject"):
            title = pick(row, "title").strip()
            if not title:
                continue
            n += 1
            if dry:
                continue
            slug = pick(row, "slug").strip() or slugify_fallback(title)
            img = media_file_field(pick(row, "featured_image"))
            defaults = {
                "title": title,
                "project_type": pick(row, "project_type") or "residential",
                "location": pick(row, "location") or "",
                "client_name": pick(row, "client_name") or "",
                "description": pick(row, "description") or "",
                "is_featured": as_bool(pick(row, "is_featured")),
                "is_active": as_bool(pick(row, "is_active"), True),
            }
            if img:
                defaults["featured_image"] = img
            obj, _ = PortfolioProject.objects.update_or_create(slug=slug, defaults=defaults)
            if row.get("id"):
                maps["portfolio"][row["id"]] = obj

        g = 0
        for row in read_csv(data_dir, "portfolio_portfolioimage"):
            if dry:
                g += 1
                continue
            project = maps["portfolio"].get(row.get("project_id"))
            img = media_file_field(pick(row, "image"))
            if not project or not img:
                continue
            PortfolioImage.objects.get_or_create(
                project=project,
                image=img,
                defaults={
                    "caption": pick(row, "caption", default=""),
                    "alt_text": pick(row, "alt_text", default=""),
                    "display_order": as_int(pick(row, "display_order"), 0),
                },
            )
            g += 1
        self.stdout.write(f"  portfolio: {n}, gallery: {g}")

    def _step_newsletter(self, data_dir: Path, maps: dict, dry: bool) -> None:
        from home.models import NewsletterSubscriber

        self.stdout.write("--- Newsletter subscribers ---")
        n = 0
        for row in read_csv(data_dir, "home_newslettersubscriber"):
            email = pick(row, "email").strip().lower()
            if not email:
                continue
            n += 1
            if not dry:
                NewsletterSubscriber.objects.get_or_create(email=email)
        self.stdout.write(f"  subscribers: {n}")

    def _step_users(self, data_dir: Path, maps: dict, dry: bool) -> None:
        """Optional — imports staff/customers if accounts_user.csv exists."""
        self.stdout.write("--- Users (optional) ---")
        rows = read_csv(data_dir, "accounts_user")
        if not rows:
            self.stdout.write("  no accounts_user.csv — skip")
            return
        n = 0
        for row in rows:
            username = pick(row, "username").strip()
            if not username:
                continue
            n += 1
            if dry:
                continue
            email = pick(row, "email") or ""
            defaults = {
                "email": email,
                "full_name": pick(row, "full_name") or "",
                "phone": pick(row, "phone") or "",
                "role": pick(row, "role") or User.Roles.CUSTOMER,
                "is_active": as_bool(pick(row, "is_active"), True),
                "is_staff": as_bool(pick(row, "is_staff")),
                "is_superuser": as_bool(pick(row, "is_superuser")),
                "is_email_verified": as_bool(pick(row, "is_email_verified")),
                "is_phone_verified": as_bool(pick(row, "is_phone_verified")),
            }
            user, created = User.objects.update_or_create(username=username, defaults=defaults)
            password_hash = pick(row, "password")
            if password_hash and (created or not user.password):
                user.password = password_hash
                user.save(update_fields=["password"])
        self.stdout.write(f"  users: {n} (passwords preserved if hash in CSV)")
