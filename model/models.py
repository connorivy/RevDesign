from django.db import models

class Member(models.Model):
    id = models.CharField(max_length=20)
    shape = models.CharField(max_length=15)
    node1 = {
        models.CharField(max_length=15),
        models.CharField(max_length=15),
        models.CharField(max_length=15),
    }
    node2 = {
        models.CharField(max_length=15),
        models.CharField(max_length=15),
        models.CharField(max_length=15),
    }

    BoolType = models.TextChoices('MedalType', 'True False')

    designed = models.CharField(blank=True, choices=BoolType.choices, max_length=10)

    last_modified_at = models.DateTimeField()

    last_modified_by = models.CharField()