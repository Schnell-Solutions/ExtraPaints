import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('colors', '0002_remove_color_available_finishes_and_more'),
        ('products', '0004_alter_product_coats_required'),
    ]

    operations = [
        migrations.CreateModel(
            name='Guide',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(blank=True, max_length=180, unique=True)),
                ('guide_type', models.CharField(choices=[('article', 'Article'), ('howto', 'How-To'), ('faq', 'FAQ')], default='article', max_length=20)),
                ('excerpt', models.TextField(help_text='Short summary for listings and meta description fallback.')),
                ('body', models.TextField()),
                ('meta_description', models.CharField(blank=True, max_length=320)),
                ('faq_items', models.JSONField(blank=True, default=list, help_text='List of {"question": "...", "answer": "..."} objects.')),
                ('howto_steps', models.JSONField(blank=True, default=list, help_text='List of {"name": "...", "text": "..."} for HowTo schema.')),
                ('howto_total_time', models.CharField(blank=True, default='PT1H', help_text='ISO 8601 duration, e.g. PT30M, PT1H', max_length=30)),
                ('is_published', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('related_colors', models.ManyToManyField(blank=True, related_name='guides', to='colors.color')),
                ('related_products', models.ManyToManyField(blank=True, related_name='guides', to='products.product')),
            ],
            options={
                'verbose_name': 'Guide',
                'verbose_name_plural': 'Guides',
                'ordering': ['-is_featured', '-updated_at'],
            },
        ),
    ]
