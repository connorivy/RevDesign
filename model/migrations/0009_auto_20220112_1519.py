# Generated by Django 3.2.5 on 2022-01-12 21:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('model', '0008_auto_20220112_1026'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='new_node1',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='new_node1', to='model.node'),
        ),
        migrations.AlterField(
            model_name='member',
            name='new_node2',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='new_node2', to='model.node'),
        ),
    ]
