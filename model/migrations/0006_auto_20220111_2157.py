# Generated by Django 3.2.5 on 2022-01-12 03:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('model', '0005_auto_20220111_2139'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='designed',
        ),
        migrations.RemoveField(
            model_name='member',
            name='last_modified_at',
        ),
        migrations.RemoveField(
            model_name='member',
            name='last_modified_by',
        ),
        migrations.RemoveField(
            model_name='member',
            name='shape',
        ),
    ]
