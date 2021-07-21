from django.db import models
from django.contrib.auth.models import User

class Member(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    shape = models.CharField(max_length=25)

    node1x = models.DecimalField(max_digits=14, decimal_places=10)
    node1y = models.DecimalField(max_digits=14, decimal_places=10)
    node1z = models.DecimalField(max_digits=14, decimal_places=10)

    node2x = models.DecimalField(max_digits=14, decimal_places=10)
    node2y = models.DecimalField(max_digits=14, decimal_places=10)
    node2z = models.DecimalField(max_digits=14, decimal_places=10)

    # BoolType = models.TextChoices('MedalType', 'True False')
    # designed = models.CharField(blank=True, choices=BoolType.choices, max_length=10)
    designed = models.BooleanField()

    last_modified_at = models.DateTimeField(auto_now=True)

    last_modified_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.id}, {self.shape}'