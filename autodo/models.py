from django.db import models
from django.contrib.auth.models import AbstractUser
from djmoney.models.fields import MoneyField


class Greeting(models.Model):
    when = models.DateTimeField("date created", auto_now_add=True)


class User(AbstractUser):
    ROLE_CHOICES = [
        ("DRIVER", "Driver"),
        ("OWNER_MANAGER", "Owner/Manager"),
        ("TRANSPORT_OFFICER", "Motor Transport Officer"),
    ]

    email_notifications = models.BooleanField(default=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="DRIVER")

    @property
    def can_manage_maintenance(self):
        return self.is_staff or self.role in {"OWNER_MANAGER", "TRANSPORT_OFFICER"}

    @property
    def can_manage_fuel_rates(self):
        return self.is_staff or self.role in {"OWNER_MANAGER", "TRANSPORT_OFFICER"}

    class Meta:
        db_table = "auth_user"


class OdomSnapshot(models.Model):
    car = models.ForeignKey(
        "Car", null=True, related_name="snaps", on_delete=models.CASCADE
    )
    owner = models.ForeignKey(
        "User", related_name="odomSnapshot", on_delete=models.CASCADE
    )
    date = models.DateTimeField()
    mileage = models.FloatField()

    class Meta:
        ordering = ["-mileage"]


class Todo(models.Model):
    owner = models.ForeignKey("User", related_name="todo", on_delete=models.CASCADE)
    car = models.ForeignKey("Car", on_delete=models.CASCADE)
    completionOdomSnapshot = models.ForeignKey(
        "OdomSnapshot", on_delete=models.SET_NULL, blank=True, null=True
    )
    name = models.CharField(max_length=32, null=False)
    complete = models.BooleanField(default=False)
    dueMileage = models.FloatField(default=None, blank=True, null=True)
    dueDate = models.DateTimeField(default=None, blank=True, null=True)
    notes = models.TextField(default=None, blank=True, null=True)
    estimatedDueDate = models.BooleanField(default=False, blank=True, null=True)
    mileageRepeatInterval = models.FloatField(default=None, blank=True, null=True)
    daysRepeatInterval = models.IntegerField(default=None, blank=True, null=True)
    monthsRepeatInterval = models.IntegerField(default=None, blank=True, null=True)
    yearsRepeatInterval = models.IntegerField(default=None, blank=True, null=True)

    class Meta:
        ordering = ["dueDate", "dueMileage"]


class Car(models.Model):
    TRANSMISSION_CHOICES = [("AUTO", "Automatic"), ("MANUAL", "Manual")]
    FUEL_TYPE_CHOICES = [
        ("PMS", "PMS"),
        ("AGO", "AGO"),
        ("HYBRID", "Hybrid"),
        ("EV", "Electric"),
    ]
    STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("DEPLOYED", "Deployed"),
        ("MAINTENANCE", "Maintenance"),
        ("DOWN", "Down"),
        ("INACTIVE", "Inactive"),
    ]

    owner = models.ForeignKey(User, related_name="car", on_delete=models.CASCADE)
    name = models.CharField(max_length=32, null=False)
    make = models.CharField(max_length=32, blank=True, null=True)
    model = models.CharField(max_length=32, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    plate = models.CharField(max_length=10, blank=True, null=True)
    vin = models.CharField(max_length=10, blank=True, null=True)
    transmission = models.CharField(max_length=10, choices=TRANSMISSION_CHOICES, default="AUTO")
    fuel_type = models.CharField(max_length=10, choices=FUEL_TYPE_CHOICES, default="PMS")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="AVAILABLE")
    specs = models.TextField(blank=True, null=True)
    inspection_interval_days = models.PositiveIntegerField(blank=True, null=True)
    servicing_interval_days = models.PositiveIntegerField(blank=True, null=True)
    last_service_date = models.DateField(blank=True, null=True)
    next_service_due_date = models.DateField(blank=True, null=True)
    replacement_schedule = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7)

    @property
    def light_color(self):
        r = int(self.color[1:3], base=16)
        g = int(self.color[3:5], base=16)
        b = int(self.color[5:7], base=16)
        luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return luma > 150


class FuelPriceConfig(models.Model):
    fuel_type = models.CharField(max_length=10, choices=Car.FUEL_TYPE_CHOICES, unique=True)
    price_per_litre = MoneyField(max_digits=8, decimal_places=2, default_currency="USD")


class TyreRecord(models.Model):
    owner = models.ForeignKey(User, related_name="tyre_records", on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name="tyre_records", on_delete=models.CASCADE)
    position = models.CharField(max_length=20)
    manufacturer = models.CharField(max_length=64, blank=True, null=True)
    manufacture_date = models.DateField(blank=True, null=True)
    installation_date = models.DateField(blank=True, null=True)
    life_span_km = models.FloatField(blank=True, null=True)
    replacement_due_date = models.DateField(blank=True, null=True)
    inspection_interval_days = models.PositiveIntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)


class BatteryRecord(models.Model):
    owner = models.ForeignKey(User, related_name="battery_records", on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name="battery_records", on_delete=models.CASCADE)
    manufacturer = models.CharField(max_length=64, blank=True, null=True)
    manufacture_date = models.DateField(blank=True, null=True)
    installation_date = models.DateField(blank=True, null=True)
    life_span_days = models.PositiveIntegerField(blank=True, null=True)
    replacement_due_date = models.DateField(blank=True, null=True)
    inspection_interval_days = models.PositiveIntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)


class CriticalPartInspection(models.Model):
    PART_CHOICES = [
        ("BRAKES", "Brakes"),
        ("ENGINE", "Engine"),
        ("TRANSMISSION", "Transmission"),
        ("TYRES", "Tyres"),
        ("BATTERY", "Battery"),
        ("COOLING", "Cooling System"),
        ("SUSPENSION", "Suspension"),
    ]
    CONDITION_CHOICES = [
        ("GOOD", "Good"),
        ("ATTENTION", "Needs Attention"),
        ("CRITICAL", "Critical"),
    ]

    owner = models.ForeignKey(User, related_name="critical_part_checks", on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name="critical_part_checks", on_delete=models.CASCADE)
    checked_at = models.DateTimeField()
    part = models.CharField(max_length=20, choices=PART_CHOICES)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default="GOOD")
    notes = models.TextField(blank=True, null=True)
    estimated_repair_cost = MoneyField(max_digits=8, decimal_places=2, default_currency="USD", blank=True, null=True)

    class Meta:
        ordering = ["-checked_at"]


class DailyChecklist(models.Model):
    owner = models.ForeignKey(User, related_name="daily_checklists", on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name="daily_checklists", on_delete=models.CASCADE)
    date = models.DateField()
    before_driving_notes = models.TextField(blank=True, null=True)
    after_driving_notes = models.TextField(blank=True, null=True)
    odometer_before_km = models.FloatField(blank=True, null=True)
    odometer_after_km = models.FloatField(blank=True, null=True)
    water_level_ok = models.BooleanField(default=True)
    engine_oil_ok = models.BooleanField(default=True)
    coolant_ok = models.BooleanField(default=True)
    brake_fluid_ok = models.BooleanField(default=True)
    tyre_pressure_ok = models.BooleanField(default=True)

    class Meta:
        ordering = ["-date"]


class ServiceRecord(models.Model):
    owner = models.ForeignKey(User, related_name="service_records", on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name="service_records", on_delete=models.CASCADE)
    service_date = models.DateField()
    service_type = models.CharField(max_length=64)
    provider = models.CharField(max_length=128, blank=True, null=True)
    mileage_km = models.FloatField(blank=True, null=True)
    total_cost = MoneyField(max_digits=10, decimal_places=2, default_currency="USD", blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-service_date"]


class IncidentReport(models.Model):
    owner = models.ForeignKey(User, related_name="incident_reports", on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name="incident_reports", on_delete=models.CASCADE)
    date = models.DateTimeField()
    incident_type = models.CharField(max_length=64, default="Defect")
    details = models.TextField()
    status = models.CharField(max_length=32, default="Open")
    reported_by = models.ForeignKey(User, related_name="reported_incidents", on_delete=models.SET_NULL, null=True, blank=True)
    estimated_cost = MoneyField(max_digits=10, decimal_places=2, default_currency="USD", blank=True, null=True)
    actual_cost = MoneyField(max_digits=10, decimal_places=2, default_currency="USD", blank=True, null=True)
    downtime_start = models.DateTimeField(blank=True, null=True)
    downtime_end = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-date"]


class DeploymentRecord(models.Model):
    owner = models.ForeignKey(User, related_name="deployment_records", on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name="deployment_records", on_delete=models.CASCADE)
    start_point = models.CharField(max_length=128)
    end_point = models.CharField(max_length=128)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    gps_distance_km = models.FloatField(blank=True, null=True)
    start_odometer_km = models.FloatField(blank=True, null=True)
    end_odometer_km = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ["-start_time"]


class DriverStyleRecord(models.Model):
    owner = models.ForeignKey(User, related_name="driver_style_records", on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name="driver_style_records", on_delete=models.CASCADE)
    recorded_at = models.DateTimeField()
    acceleration_events = models.PositiveIntegerField(default=0)
    deceleration_events = models.PositiveIntegerField(default=0)
    harsh_braking_events = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-recorded_at"]


class Refueling(models.Model):
    owner = models.ForeignKey(User, related_name="refueling", on_delete=models.CASCADE)
    odomSnapshot = models.ForeignKey(OdomSnapshot, on_delete=models.CASCADE)
    cost = MoneyField(max_digits=6, decimal_places=2, default_currency="USD")
    amount = models.FloatField()
