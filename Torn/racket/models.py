from django.db import models


class Territory(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=100)  # Added name field

    def __str__(self):
        return self.code


class Racket(models.Model):
    territory = models.ForeignKey(Territory, to_field='code', on_delete=models.CASCADE)  # Link to territory.code
    name = models.CharField(max_length=100)
    level = models.IntegerField()
    reward = models.CharField(max_length=100)
    created = models.DateTimeField()
    changed = models.DateTimeField()
    faction = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
