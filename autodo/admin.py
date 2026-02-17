from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User,
    Car,
    OdomSnapshot,
    Refueling,
    Todo,
    FuelPriceConfig,
    TyreRecord,
    BatteryRecord,
    DailyChecklist,
    IncidentReport,
    DeploymentRecord,
    DriverStyleRecord,
    CriticalPartInspection,
    ServiceRecord,
)

admin.site.register(User, UserAdmin)
admin.site.register(Car)
admin.site.register(OdomSnapshot)
admin.site.register(Refueling)
admin.site.register(Todo)
admin.site.register(FuelPriceConfig)
admin.site.register(TyreRecord)
admin.site.register(BatteryRecord)
admin.site.register(DailyChecklist)
admin.site.register(IncidentReport)
admin.site.register(DeploymentRecord)
admin.site.register(DriverStyleRecord)
admin.site.register(CriticalPartInspection)
admin.site.register(ServiceRecord)
