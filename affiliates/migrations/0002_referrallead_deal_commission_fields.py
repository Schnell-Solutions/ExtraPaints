from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('affiliates', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='referrallead',
            name='commission_amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Partner commission amount in KES (optional).',
                max_digits=12,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='referrallead',
            name='commission_status',
            field=models.CharField(
                choices=[
                    ('na', 'Not applicable'),
                    ('pending', 'Pending'),
                    ('approved', 'Approved'),
                    ('paid', 'Paid'),
                ],
                db_index=True,
                default='na',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='referrallead',
            name='conversion_notes',
            field=models.TextField(
                blank=True,
                help_text='Internal notes: follow-ups, PO numbers, commission terms, etc.',
            ),
        ),
        migrations.AddField(
            model_name='referrallead',
            name='conversion_status',
            field=models.CharField(
                choices=[
                    ('new', 'New lead'),
                    ('qualified', 'Qualified'),
                    ('quoted', 'Quote sent'),
                    ('won', 'Won / converted'),
                    ('lost', 'Lost'),
                ],
                db_index=True,
                default='new',
                help_text='Internal pipeline status (admin only).',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='referrallead',
            name='deal_value',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Estimated or closed deal value in KES (optional).',
                max_digits=12,
                null=True,
            ),
        ),
    ]
