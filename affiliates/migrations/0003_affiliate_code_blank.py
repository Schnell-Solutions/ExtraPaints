from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('affiliates', '0002_referrallead_deal_commission_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='affiliate',
            name='code',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Auto-generated on save (format: NAME-XXXX). Staff should not type this manually.',
                max_length=32,
                unique=True,
            ),
        ),
    ]
