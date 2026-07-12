from datetime import date

from django.test import SimpleTestCase

from core.brand import company_years_experience, format_kenya_phone_local, format_whatsapp_display


class BrandHelpersTests(SimpleTestCase):
    def test_years_experience_from_founding_year(self):
        self.assertEqual(company_years_experience(date(2026, 5, 21)), 11)

    def test_whatsapp_display_format(self):
        self.assertEqual(
            format_whatsapp_display('254725752908'),
            '0725 752 908',
        )

    def test_kenya_phone_local_format(self):
        self.assertEqual(format_kenya_phone_local('+254725752908'), '0725 752 908')
