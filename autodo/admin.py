from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
from .models import (
    User,
    Car,
    OdomSnapshot,
    Refueling,
    Todo,
    AssetComponent,
    MaintenanceSchedule,
    MaintenanceRequirement,
    DefectReport,
    WorkOrder,
    WorkOrderRequirement,
    WorkOrderAction,
    PartReplacement,
)

admin.site.register(User, UserAdmin)
admin.site.register(Car)
admin.site.register(OdomSnapshot)
admin.site.register(Refueling)
admin.site.register(Todo)
admin.site.register(AssetComponent)
admin.site.register(MaintenanceSchedule)
admin.site.register(MaintenanceRequirement)
admin.site.register(DefectReport)
admin.site.register(WorkOrder)
admin.site.register(WorkOrderRequirement)
admin.site.register(WorkOrderAction)
admin.site.register(PartReplacement)
