from django.db import models


class Rackets(models.Model):
    territory = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    level = models.IntegerField()
    reward = models.IntegerField()
    created = models.DateTimeField()
    changed = models.DateTimeField()
    faction = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)  # This line for the timestamp

    def __str__(self):
        return self.name
    