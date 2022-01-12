from django.db import models
from django.contrib.auth.models import User
from django.db.models.base import Model
from django.db.models.deletion import CASCADE
class node(models.Model):
    # This is what you would increment on save
    # Default this to one as a starting point
    display_id = models.IntegerField(default=1)

    x = models.DecimalField(max_digits=14, decimal_places=10)
    y = models.DecimalField(max_digits=14, decimal_places=10)
    z = models.DecimalField(max_digits=14, decimal_places=10)

    # def __str__(self):
    #     return f'{self.id}'

class Member(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    type = models.CharField(max_length=25)

    node1 = models.ForeignKey(node, on_delete=models.CASCADE, related_name='node1')
    node2 = models.ForeignKey(node, on_delete=models.CASCADE, related_name='node2')

    new_node1 = models.ForeignKey(node, on_delete=models.CASCADE, related_name='new_node1', null=True, blank=True)
    new_node2 = models.ForeignKey(node, on_delete=models.CASCADE, related_name='new_node2', null=True, blank=True)


    def __str__(self):
        return f'{self.id}'