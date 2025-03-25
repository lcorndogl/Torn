from django.db import models

class Faction(models.Model):
    faction_id = models.IntegerField()
    name = models.CharField(max_length=255)
    tag = models.CharField(max_length=5)
    respect = models.IntegerField()

    def __str__(self):
        return self.name
