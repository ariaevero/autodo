from django.db import models
from django.contrib.auth.models import AbstractUser
from djmoney.models.fields import MoneyField

# Create your models here.
class Greeting(models.Model):
    when = models.DateTimeField("date created", auto_now_add=True)


class User(AbstractUser):
    email_notifications = models.BooleanField(default=True)

    class Meta:
        db_table = "auth_user"


class OdomSnapshot(models.Model):
    """The relevant data for an update to a car's odometer reading."""

    car = models.ForeignKey(
        "Car", null=True, related_name="snaps", on_delete=models.CASCADE
    )
    owner = models.ForeignKey(
        "User", related_name="odomSnapshot", on_delete=models.CASCADE
    )

    date = models.DateTimeField()
    mileage = models.FloatField()

    def __str__(self):
        return f"{self.owner}'s Odometer Snapshot for car: {self.car} on: {self.date} at: {self.mileage}"

    class Meta:
        ordering = ["-mileage"]


class Todo(models.Model):
    """A task or action to perform on a car."""

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
    # TODO: calculate this on POST
    estimatedDueDate = models.BooleanField(default=False, blank=True, null=True)
    mileageRepeatInterval = models.FloatField(default=None, blank=True, null=True)
    daysRepeatInterval = models.IntegerField(default=None, blank=True, null=True)
    monthsRepeatInterval = models.IntegerField(default=None, blank=True, null=True)
    yearsRepeatInterval = models.IntegerField(default=None, blank=True, null=True)

    def __str__(self):
        return f"Todo {self.id} named: {self.name} due at {self.dueMileage} miles"

    class Meta:
        ordering = ["dueDate", "dueMileage"]


class Car(models.Model):
    """Represents the data for a Car type."""

    owner = models.ForeignKey(User, related_name="car", on_delete=models.CASCADE)

    name = models.CharField(max_length=32, null=False)
    make = models.CharField(max_length=32, blank=True, null=True)
    model = models.CharField(max_length=32, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    plate = models.CharField(max_length=10, blank=True, null=True)
    vin = models.CharField(max_length=10, blank=True, null=True)
    # image = models.ImageField(upload_to="cars", null=True)
    color = models.CharField(max_length=7)  # TODO: autodo green to int maybe?

    @property
    def light_color(self):
        r = int(self.color[1:3], base=16)
        g = int(self.color[3:5], base=16)
        b = int(self.color[5:7], base=16)
        luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return luma > 150

    def __str__(self):
        return "Car named: {}".format(self.name)


class Refueling(models.Model):
    """Data associated with a car's refueling event."""

    owner = models.ForeignKey(User, related_name="refueling", on_delete=models.CASCADE)
    odomSnapshot = models.ForeignKey(OdomSnapshot, on_delete=models.CASCADE)

    cost = MoneyField(max_digits=6, decimal_places=2, default_currency="USD")
    amount = models.FloatField()

    def __str__(self):
        return f"Refueling {self.id} for cost: {self.cost} and amount: {self.amount} with snap: {self.odomSnapshot.id}"


class AssetComponent(models.Model):
    """A serialized asset component installed on a car."""

    class LifecycleStatus(models.TextChoices):
        IN_SERVICE = "in_service", "In Service"
        SPARE = "spare", "Spare"
        UNDER_REPAIR = "under_repair", "Under Repair"
        REMOVED = "removed", "Removed"
        SCRAPPED = "scrapped", "Scrapped"

    owner = models.ForeignKey(User, related_name="asset_component", on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name="components", on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    serial_number = models.CharField(max_length=120)
    manufacturer = models.CharField(max_length=120, blank=True, null=True)
    installed_at = models.DateTimeField(blank=True, null=True)
    removed_at = models.DateTimeField(blank=True, null=True)
    lifecycle_status = models.CharField(
        max_length=24,
        choices=LifecycleStatus.choices,
        default=LifecycleStatus.IN_SERVICE,
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "serial_number"],
                name="uniq_component_serial_per_owner",
            )
        ]
        ordering = ["name", "serial_number"]

    def __str__(self):
        return f"{self.name} ({self.serial_number})"


class MaintenanceSchedule(models.Model):
    """Defines recurrence and due rules for preventive maintenance."""

    owner = models.ForeignKey(
        User, related_name="maintenance_schedule", on_delete=models.CASCADE
    )
    car = models.ForeignKey(Car, related_name="maintenance_schedule", on_delete=models.CASCADE)
    component = models.ForeignKey(
        AssetComponent,
        related_name="maintenance_schedule",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    interval_days = models.PositiveIntegerField(blank=True, null=True)
    interval_mileage = models.FloatField(blank=True, null=True)
    last_performed_date = models.DateTimeField(blank=True, null=True)
    last_performed_mileage = models.FloatField(blank=True, null=True)
    next_due_date = models.DateTimeField(blank=True, null=True)
    next_due_mileage = models.FloatField(blank=True, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["next_due_date", "next_due_mileage", "title"]

    def __str__(self):
        return f"Schedule {self.title} for {self.car.name}"


class MaintenanceRequirement(models.Model):
    """Checklist requirements attached to a schedule."""

    owner = models.ForeignKey(
        User, related_name="maintenance_requirement", on_delete=models.CASCADE
    )
    schedule = models.ForeignKey(
        MaintenanceSchedule,
        related_name="requirements",
        on_delete=models.CASCADE,
    )
    code = models.CharField(max_length=32, blank=True, null=True)
    title = models.CharField(max_length=120)
    details = models.TextField(blank=True, null=True)
    mandatory = models.BooleanField(default=True)
    sequence = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["sequence", "id"]

    def __str__(self):
        return self.title


class DefectReport(models.Model):
    """Issue or anomaly observed against a car/component."""

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        TRIAGED = "triaged", "Triaged"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    owner = models.ForeignKey(User, related_name="defect_report", on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name="defect_report", on_delete=models.CASCADE)
    component = models.ForeignKey(
        AssetComponent,
        related_name="defect_report",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    reported_by = models.ForeignKey(
        User,
        related_name="reported_defect_report",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=140)
    description = models.TextField()
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    detected_at = models.DateTimeField()
    resolved_at = models.DateTimeField(blank=True, null=True)
    root_cause = models.TextField(blank=True, null=True)
    corrective_action = models.TextField(blank=True, null=True)
    preventive_action = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-detected_at"]

    def __str__(self):
        return self.title


class WorkOrder(models.Model):
    """Maintenance execution container with approval + completion flow."""

    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        APPROVED = "approved", "Approved"
        IN_PROGRESS = "in_progress", "In Progress"
        ON_HOLD = "on_hold", "On Hold"
        COMPLETED = "completed", "Completed"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    owner = models.ForeignKey(User, related_name="work_order", on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name="work_order", on_delete=models.CASCADE)
    component = models.ForeignKey(
        AssetComponent,
        related_name="work_order",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    schedule = models.ForeignKey(
        MaintenanceSchedule,
        related_name="work_order",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    defect_report = models.ForeignKey(
        DefectReport,
        related_name="work_order",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=140)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PLANNED)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIUM)
    opened_at = models.DateTimeField()
    due_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    assigned_to = models.ForeignKey(
        User,
        related_name="assigned_work_order",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    created_by = models.ForeignKey(
        User,
        related_name="created_work_order",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-opened_at"]

    def __str__(self):
        return self.title


class WorkOrderRequirement(models.Model):
    """Requirement checklist line item tied to work order."""

    owner = models.ForeignKey(
        User, related_name="work_order_requirement", on_delete=models.CASCADE
    )
    work_order = models.ForeignKey(
        WorkOrder,
        related_name="requirements",
        on_delete=models.CASCADE,
    )
    requirement = models.ForeignKey(
        MaintenanceRequirement,
        related_name="work_order_requirement",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=140)
    details = models.TextField(blank=True, null=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]


class WorkOrderAction(models.Model):
    """Audit trail for actions completed against work orders."""

    owner = models.ForeignKey(User, related_name="work_order_action", on_delete=models.CASCADE)
    work_order = models.ForeignKey(
        WorkOrder,
        related_name="actions",
        on_delete=models.CASCADE,
    )
    performed_by = models.ForeignKey(
        User,
        related_name="performed_work_order_action",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    performed_at = models.DateTimeField()
    notes = models.TextField()

    class Meta:
        ordering = ["performed_at"]


class PartReplacement(models.Model):
    """Replacement history for serialized parts and consumables."""

    owner = models.ForeignKey(User, related_name="part_replacement", on_delete=models.CASCADE)
    work_order = models.ForeignKey(
        WorkOrder,
        related_name="part_replacements",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    car = models.ForeignKey(Car, related_name="part_replacement", on_delete=models.CASCADE)
    component = models.ForeignKey(
        AssetComponent,
        related_name="part_replacement",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    part_name = models.CharField(max_length=120)
    part_serial_number = models.CharField(max_length=120, blank=True, null=True)
    replaced_at = models.DateTimeField()
    odometer_mileage = models.FloatField(blank=True, null=True)
    supplier = models.CharField(max_length=120, blank=True, null=True)
    cost_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ["-replaced_at"]
