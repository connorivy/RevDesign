# Generated by Django 3.2.5 on 2022-01-12 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('model', '0006_auto_20220111_2157'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='modified',
            field=models.BooleanField(default=False),
        ),
    ]
