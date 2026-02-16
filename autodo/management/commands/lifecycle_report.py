import json

from django.core.management.base import BaseCommand, CommandError

from autodo.models import (
    User,
    AssetComponent,
    MaintenanceSchedule,
    DefectReport,
    WorkOrder,
    PartReplacement,
)


class Command(BaseCommand):
    help = "Print a lifecycle summary JSON report for a username"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)

    def handle(self, *args, **options):
        username = options["username"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(f"Unknown user: {username}") from exc

        payload = {
            "username": user.username,
            "components": AssetComponent.objects.filter(owner=user).count(),
            "active_schedules": MaintenanceSchedule.objects.filter(
                owner=user, active=True
            ).count(),
            "open_defects": DefectReport.objects.filter(owner=user).exclude(
                status__in=[DefectReport.Status.RESOLVED, DefectReport.Status.CLOSED]
            ).count(),
            "open_work_orders": WorkOrder.objects.filter(owner=user).exclude(
                status__in=[WorkOrder.Status.COMPLETED, WorkOrder.Status.CLOSED]
            ).count(),
            "replacements": PartReplacement.objects.filter(owner=user).count(),
        }
        self.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
