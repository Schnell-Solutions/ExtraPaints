from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideas', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Category',
            new_name='IdeaCategory',
        ),
        migrations.AlterModelOptions(
            name='ideacategory',
            options={
                'verbose_name': 'Idea category',
                'verbose_name_plural': 'Idea categories',
                'ordering': ['name'],
            },
        ),
    ]
