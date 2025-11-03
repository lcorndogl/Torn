from django.db import models


class Company(models.Model):
    company_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)


class Employee(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    employee_id = models.IntegerField()
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    wage = models.BigIntegerField(null=True, blank=True)  # Using BigIntegerField for large wage values
    manual_labour = models.IntegerField()
    intelligence = models.IntegerField()
    endurance = models.IntegerField()
    effectiveness_working_stats = models.IntegerField()
    effectiveness_settled_in = models.IntegerField()
    effectiveness_merits = models.IntegerField(default=0)
    effectiveness_director_education = models.IntegerField()
    effectiveness_management = models.IntegerField()
    effectiveness_inactivity = models.IntegerField()
    effectiveness_addiction = models.IntegerField(default=0)
    effectiveness_total = models.IntegerField()
    last_action_status = models.CharField(max_length=255)
    last_action_timestamp = models.DateTimeField()
    last_action_relative = models.CharField(max_length=255)
    status_description = models.CharField(max_length=255)
    status_state = models.CharField(max_length=255)
    status_until = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        pass
