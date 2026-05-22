from datetime import date

from django.test import SimpleTestCase

from core.brand import company_years_experience, format_whatsapp_display


class BrandHelpersTests(SimpleTestCase):
    def test_years_experience_from_founding_year(self):
        self.assertEqual(company_years_experience(date(2026, 5, 21)), 11)

    def test_whatsapp_display_format(self):
        self.assertEqual(
            format_whatsapp_display('254750422863'),
            '+254 750 422 863',
        )
