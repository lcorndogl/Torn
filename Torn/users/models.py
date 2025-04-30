from django.db import models

class UserList(models.Model):
    user_id = models.IntegerField(primary_key=True)
    game_name = models.CharField(max_length=255)

    def __str__(self):
        return self.game_name

class UserRecord(models.Model):
    user_id = models.ForeignKey(UserList, on_delete=models.CASCADE, to_field='user_id')
    name = models.CharField(max_length=255)
    level = models.IntegerField()
    days_in_faction = models.IntegerField()
    last_action_status = models.CharField(max_length=255)
    last_action_timestamp = models.IntegerField()
    last_action_relative = models.CharField(max_length=255)
    status_description = models.CharField(max_length=255)
    status_details = models.CharField(max_length=255, blank=True)
    status_state = models.CharField(max_length=255)
    status_color = models.CharField(max_length=50)
    status_until = models.IntegerField()
    position = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)
    current_faction = models.ForeignKey('faction.FactionList', on_delete=models.CASCADE, to_field='faction_id')

    def __str__(self):
        return self.name


