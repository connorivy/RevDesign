from django.db import models
from django.contrib.auth.models import User

class Member(models.Model):
    id = models.CharField(primary_key=True, max_length=20)
    shape = models.CharField(max_length=15)

    node1x = models.CharField(max_length=15),
    node1y = models.CharField(max_length=15),
    node1z = models.CharField(max_length=15),

    node2x = models.CharField(max_length=15),
    node2y = models.CharField(max_length=15),
    node2z = models.CharField(max_length=15),

    BoolType = models.TextChoices('MedalType', 'True False')

    designed = models.CharField(blank=True, choices=BoolType.choices, max_length=10)

    last_modified_at = models.DateTimeField(auto_now=True)

    last_modified_by = models.ForeignKey(User, on_delete=models.CASCADE)

def __str__(self):
   return self.id, self.shape 