from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountDeletionRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_snapshot', models.EmailField(max_length=254)),
                ('username_snapshot', models.CharField(max_length=150)),
                ('full_name_snapshot', models.CharField(blank=True, max_length=200)),
                ('reason', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pending review'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], db_index=True, default='pending', max_length=20)),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deletion_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Account deletion request',
                'verbose_name_plural': 'Account deletion requests',
                'ordering': ['-requested_at'],
            },
        ),
    ]
