# Generated by Django 3.2.5 on 2022-01-12 16:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('model', '0007_member_modified'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='modified',
        ),
        migrations.AddField(
            model_name='member',
            name='new_node1',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='new_node1', to='model.node'),
        ),
        migrations.AddField(
            model_name='member',
            name='new_node2',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='new_node2', to='model.node'),
        ),
    ]
