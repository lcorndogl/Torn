from django.db import models


class FactionList(models.Model):
    faction_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    tag = models.CharField(max_length=5)

    def __str__(self):
        return self.name


class Faction(models.Model):
    faction_id = models.ForeignKey(
        FactionList, on_delete=models.CASCADE, to_field='faction_id'
    )
    respect = models.IntegerField()
    rank = models.CharField(max_length=50, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.faction_id.name


class OrganisedCrimeRole(models.Model):
    crime_name = models.CharField(max_length=255)
    level = models.CharField(max_length=50)
    role = models.CharField(max_length=50)
    required_cpr = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.crime_name} - {self.role}"
