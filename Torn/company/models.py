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
    created_on = models.DateTimeField()  # Remove auto_now_add to allow manual setting

    class Meta:
        pass


class CurrentEmployee(models.Model):
    """Model to track current employees in companies"""
    user_id = models.IntegerField()
    username = models.CharField(max_length=255)
    company_id = models.IntegerField()
    company_name = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user_id', 'company_id']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['company_id']),
        ]

    def __str__(self):
        return f"{self.username} - {self.company_name}"


class DailyEmployeeSnapshot(models.Model):
    """Model to store one record per day per employee with all employee data"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    employee_id = models.IntegerField()
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    wage = models.BigIntegerField(null=True, blank=True)
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
    snapshot_date = models.DateField()  # The date this snapshot was taken
    created_on = models.DateTimeField(auto_now_add=True)  # When this record was created
    modified_on = models.DateTimeField(auto_now=True)  # When this record was last updated
    
    # Travel tracking fields for Switzerland
    last_travelled_to_switzerland = models.DateTimeField(null=True, blank=True)  # When employee started traveling to Switzerland
    in_switzerland = models.DateTimeField(null=True, blank=True)  # When employee arrived in Switzerland
    returning_from_switzerland = models.DateTimeField(null=True, blank=True)  # When employee started returning from Switzerland

    class Meta:
        unique_together = ['company', 'employee_id', 'snapshot_date']
        indexes = [
            models.Index(fields=['employee_id', 'snapshot_date']),
            models.Index(fields=['company', 'snapshot_date']),
            models.Index(fields=['snapshot_date']),
        ]
        ordering = ['-snapshot_date', 'name']

    def __str__(self):
        return f"{self.name} ({self.employee_id}) - {self.snapshot_date}"


class Stock(models.Model):
    """Model to track company stock values over time"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)  # e.g., "Oil (Barrel)"
    cost = models.BigIntegerField()  # Production cost
    rrp = models.BigIntegerField()  # Recommended retail price
    price = models.BigIntegerField()  # Current market price
    in_stock = models.BigIntegerField()  # Current inventory
    on_order = models.BigIntegerField()  # Quantity on order
    created_amount = models.BigIntegerField()  # Total amount created
    sold_amount = models.BigIntegerField()  # Total amount sold
    sold_worth = models.BigIntegerField()  # Total worth of sold items
    snapshot_date = models.DateField()  # Date this snapshot was taken
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['company', 'name', 'snapshot_date']
        indexes = [
            models.Index(fields=['company', 'snapshot_date']),
            models.Index(fields=['snapshot_date']),
        ]
        ordering = ['-snapshot_date', 'name']

    def __str__(self):
        return f"{self.company.name} - {self.name} ({self.snapshot_date})"
