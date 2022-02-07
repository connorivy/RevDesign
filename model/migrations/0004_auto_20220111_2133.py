# Generated by Django 3.2.5 on 2022-01-12 03:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('model', '0003_node'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='node1x',
        ),
        migrations.RemoveField(
            model_name='member',
            name='node1y',
        ),
        migrations.RemoveField(
            model_name='member',
            name='node1z',
        ),
        migrations.RemoveField(
            model_name='member',
            name='node2x',
        ),
        migrations.RemoveField(
            model_name='member',
            name='node2y',
        ),
        migrations.RemoveField(
            model_name='member',
            name='node2z',
        ),
        migrations.AddField(
            model_name='member',
            name='type',
            field=models.CharField(default=0, max_length=25),
            preserve_default=False,
        ),
    ]