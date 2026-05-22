import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Affiliate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('code', models.CharField(db_index=True, max_length=32, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Affiliate / Partner',
                'verbose_name_plural': 'Affiliates / Partners',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ReferralVisit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(blank=True, db_index=True, max_length=64)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('landing_path', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('affiliate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='visits', to='affiliates.affiliate')),
            ],
            options={
                'verbose_name': 'Referral visit',
                'verbose_name_plural': 'Referral visits',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ReferralLead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lead_type', models.CharField(choices=[('quote', 'Quote request'), ('contact', 'Contact form'), ('quick_inquiry', 'Quick inquiry')], max_length=20)),
                ('customer_name', models.CharField(max_length=200)),
                ('customer_email', models.EmailField(blank=True, max_length=254)),
                ('customer_phone', models.CharField(blank=True, max_length=30)),
                ('message_excerpt', models.CharField(blank=True, max_length=500)),
                ('referral_code_used', models.CharField(max_length=32)),
                ('session_key', models.CharField(blank=True, max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('affiliate', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='leads', to='affiliates.affiliate')),
            ],
            options={
                'verbose_name': 'Referral lead',
                'verbose_name_plural': 'Referral leads',
                'ordering': ['-created_at'],
            },
        ),
    ]
