from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("autodo", "0006_user_email_notifications"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssetComponent",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("serial_number", models.CharField(max_length=120)),
                ("manufacturer", models.CharField(blank=True, max_length=120, null=True)),
                ("installed_at", models.DateTimeField(blank=True, null=True)),
                ("removed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "lifecycle_status",
                    models.CharField(
                        choices=[
                            ("in_service", "In Service"),
                            ("spare", "Spare"),
                            ("under_repair", "Under Repair"),
                            ("removed", "Removed"),
                            ("scrapped", "Scrapped"),
                        ],
                        default="in_service",
                        max_length=24,
                    ),
                ),
                ("notes", models.TextField(blank=True, null=True)),
                (
                    "car",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="components", to="autodo.car"),
                ),
                (
                    "owner",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="asset_component", to="autodo.user"),
                ),
            ],
            options={"ordering": ["name", "serial_number"]},
        ),
        migrations.AddConstraint(
            model_name="assetcomponent",
            constraint=models.UniqueConstraint(fields=("owner", "serial_number"), name="uniq_component_serial_per_owner"),
        ),
        migrations.CreateModel(
            name="MaintenanceSchedule",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True, null=True)),
                ("interval_days", models.PositiveIntegerField(blank=True, null=True)),
                ("interval_mileage", models.FloatField(blank=True, null=True)),
                ("last_performed_date", models.DateTimeField(blank=True, null=True)),
                ("last_performed_mileage", models.FloatField(blank=True, null=True)),
                ("next_due_date", models.DateTimeField(blank=True, null=True)),
                ("next_due_mileage", models.FloatField(blank=True, null=True)),
                ("active", models.BooleanField(default=True)),
                (
                    "car",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="maintenance_schedule", to="autodo.car"),
                ),
                (
                    "component",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="maintenance_schedule", to="autodo.assetcomponent"),
                ),
                (
                    "owner",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="maintenance_schedule", to="autodo.user"),
                ),
            ],
            options={"ordering": ["next_due_date", "next_due_mileage", "title"]},
        ),
        migrations.CreateModel(
            name="MaintenanceRequirement",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(blank=True, max_length=32, null=True)),
                ("title", models.CharField(max_length=120)),
                ("details", models.TextField(blank=True, null=True)),
                ("mandatory", models.BooleanField(default=True)),
                ("sequence", models.PositiveIntegerField(default=1)),
                (
                    "owner",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="maintenance_requirement", to="autodo.user"),
                ),
                (
                    "schedule",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="requirements", to="autodo.maintenanceschedule"),
                ),
            ],
            options={"ordering": ["sequence", "id"]},
        ),
        migrations.CreateModel(
            name="DefectReport",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140)),
                ("description", models.TextField()),
                ("severity", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")], default="medium", max_length=16)),
                ("status", models.CharField(choices=[("open", "Open"), ("triaged", "Triaged"), ("in_progress", "In Progress"), ("resolved", "Resolved"), ("closed", "Closed")], default="open", max_length=16)),
                ("detected_at", models.DateTimeField()),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("root_cause", models.TextField(blank=True, null=True)),
                ("corrective_action", models.TextField(blank=True, null=True)),
                ("preventive_action", models.TextField(blank=True, null=True)),
                ("car", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="defect_report", to="autodo.car")),
                ("component", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="defect_report", to="autodo.assetcomponent")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="defect_report", to="autodo.user")),
                ("reported_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reported_defect_report", to="autodo.user")),
            ],
            options={"ordering": ["-detected_at"]},
        ),
        migrations.CreateModel(
            name="WorkOrder",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140)),
                ("description", models.TextField(blank=True, null=True)),
                ("status", models.CharField(choices=[("planned", "Planned"), ("approved", "Approved"), ("in_progress", "In Progress"), ("on_hold", "On Hold"), ("completed", "Completed"), ("closed", "Closed")], default="planned", max_length=16)),
                ("priority", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")], default="medium", max_length=16)),
                ("opened_at", models.DateTimeField()),
                ("due_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_work_order", to="autodo.user")),
                ("car", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="work_order", to="autodo.car")),
                ("component", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="work_order", to="autodo.assetcomponent")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_work_order", to="autodo.user")),
                ("defect_report", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="work_order", to="autodo.defectreport")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="work_order", to="autodo.user")),
                ("schedule", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="work_order", to="autodo.maintenanceschedule")),
            ],
            options={"ordering": ["-opened_at"]},
        ),
        migrations.CreateModel(
            name="WorkOrderRequirement",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140)),
                ("details", models.TextField(blank=True, null=True)),
                ("completed", models.BooleanField(default=False)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="work_order_requirement", to="autodo.user")),
                ("requirement", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="work_order_requirement", to="autodo.maintenancerequirement")),
                ("work_order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="requirements", to="autodo.workorder")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="WorkOrderAction",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("performed_at", models.DateTimeField()),
                ("notes", models.TextField()),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="work_order_action", to="autodo.user")),
                ("performed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="performed_work_order_action", to="autodo.user")),
                ("work_order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="actions", to="autodo.workorder")),
            ],
            options={"ordering": ["performed_at"]},
        ),
        migrations.CreateModel(
            name="PartReplacement",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("part_name", models.CharField(max_length=120)),
                ("part_serial_number", models.CharField(blank=True, max_length=120, null=True)),
                ("replaced_at", models.DateTimeField()),
                ("odometer_mileage", models.FloatField(blank=True, null=True)),
                ("supplier", models.CharField(blank=True, max_length=120, null=True)),
                ("cost_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("car", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="part_replacement", to="autodo.car")),
                ("component", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="part_replacement", to="autodo.assetcomponent")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="part_replacement", to="autodo.user")),
                ("work_order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="part_replacements", to="autodo.workorder")),
            ],
            options={"ordering": ["-replaced_at"]},
        ),
    ]
