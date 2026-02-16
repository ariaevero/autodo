import sys

from collections import defaultdict

from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django import views
from django.views import generic
from django.contrib.auth import mixins, authenticate, login

from autodo.models import (
    User,
    Car,
    Todo,
    OdomSnapshot,
    Refueling,
    AssetComponent,
    MaintenanceSchedule,
    DefectReport,
    WorkOrder,
    PartReplacement,
)
from autodo.forms import RegisterForm, SettingsForm
from autodo.filters import TodoFilter


def landing_page(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("home/?complete=False")
    return render(request, template_name="index.html")


def register(request):
    if request.method == "POST":
        f = RegisterForm(request.POST)
        if f.is_valid():
            f.save()
            new_user = authenticate(
                username=f.cleaned_data["username"],
                password=f.cleaned_data["password1"],
                email=f.cleaned_data["username"],
            )
            login(request, new_user)
            return redirect("cars")

    else:
        f = RegisterForm()

    return render(request, "registration/register.html", {"form": f})


class Stats(mixins.LoginRequiredMixin, views.View):
    def get(self, request):
        context = {"lifecycle": self._build_lifecycle_context(request.user)}
        return render(request, "autodo/stats.html", context)

    def _build_lifecycle_context(self, user):
        cars = Car.objects.filter(owner=user).order_by("name")
        components_qs = AssetComponent.objects.filter(owner=user).select_related("car")
        schedules_qs = MaintenanceSchedule.objects.filter(owner=user).select_related("car", "component")
        defects_qs = DefectReport.objects.filter(owner=user).select_related("car", "component")
        work_orders_qs = WorkOrder.objects.filter(owner=user).select_related("car", "component", "defect_report", "schedule")
        replacements_qs = PartReplacement.objects.filter(owner=user).select_related("car", "component", "work_order")
        todos = (
            Todo.objects.filter(owner=user)
            .select_related("car", "completionOdomSnapshot")
            .order_by("complete", "dueDate", "dueMileage")
        )
        refuelings = (
            Refueling.objects.filter(owner=user)
            .select_related("odomSnapshot", "odomSnapshot__car")
            .order_by("-odomSnapshot__date")
        )

        latest_snap_by_car = {}
        for snap in OdomSnapshot.objects.filter(owner=user).select_related("car").order_by(
            "car_id", "-date"
        ):
            latest_snap_by_car.setdefault(snap.car_id, snap)

        components = []
        for car in cars:
            latest_snap = latest_snap_by_car.get(car.id)
            components.append(
                {
                    "car_id": car.id,
                    "component_name": car.name,
                    "serial_number": car.vin or "UNSET",
                    "plate": car.plate,
                    "latest_odometer": latest_snap.mileage if latest_snap else None,
                    "latest_odometer_at": latest_snap.date if latest_snap else None,
                }
            )

        for component in components_qs:
            components.append(
                {
                    "car_id": component.car_id,
                    "component_name": component.name,
                    "serial_number": component.serial_number,
                    "plate": component.car.plate,
                    "latest_odometer": None,
                    "latest_odometer_at": component.installed_at,
                    "status": component.lifecycle_status,
                }
            )

        schedules_by_car = defaultdict(list)
        replacements_by_car = defaultdict(list)
        defects = []
        work_orders = []
        repair_actions = []
        requirement_links = []

        for todo in todos:
            line_item = {
                "todo_id": todo.id,
                "title": todo.name,
                "due_date": todo.dueDate,
                "due_mileage": todo.dueMileage,
                "completed": todo.complete,
                "completion_date": (
                    todo.completionOdomSnapshot.date
                    if todo.completionOdomSnapshot
                    else None
                ),
                "completion_mileage": (
                    todo.completionOdomSnapshot.mileage
                    if todo.completionOdomSnapshot
                    else None
                ),
                "requirements": todo.notes or "",
            }
            schedules_by_car[todo.car_id].append(line_item)
            if todo.complete:
                replacements_by_car[todo.car_id].append(line_item)

            notes = (todo.notes or "").lower()
            if "defect" in notes:
                defects.append(line_item)
            if "wo:" in notes or "work order" in notes:
                work_orders.append(line_item)
            if "repair" in notes or "action" in notes:
                repair_actions.append(line_item)
            if todo.notes:
                requirement_links.append(
                    {
                        "todo_id": todo.id,
                        "task": todo.name,
                        "requirements_text": todo.notes,
                    }
                )

        for schedule in schedules_qs:
            schedules_by_car[schedule.car_id].append(
                {
                    "schedule_id": schedule.id,
                    "title": schedule.title,
                    "due_date": schedule.next_due_date,
                    "due_mileage": schedule.next_due_mileage,
                    "completed": False,
                    "requirements": schedule.description or "",
                }
            )

        for replacement in replacements_qs:
            replacements_by_car[replacement.car_id].append(
                {
                    "replacement_id": replacement.id,
                    "title": replacement.part_name,
                    "completed": True,
                    "completion_date": replacement.replaced_at,
                    "completion_mileage": replacement.odometer_mileage,
                    "requirements": replacement.supplier or "",
                }
            )

        defects.extend(
            [
                {
                    "defect_id": d.id,
                    "title": d.title,
                    "severity": d.severity,
                    "status": d.status,
                    "detected_at": d.detected_at,
                }
                for d in defects_qs
            ]
        )

        work_orders.extend(
            [
                {
                    "work_order_id": w.id,
                    "title": w.title,
                    "status": w.status,
                    "priority": w.priority,
                    "opened_at": w.opened_at,
                    "due_at": w.due_at,
                }
                for w in work_orders_qs
            ]
        )

        forecast = {}
        for car in cars:
            car_refuelings = [
                r for r in refuelings if r.odomSnapshot and r.odomSnapshot.car_id == car.id
            ]
            if len(car_refuelings) >= 2:
                latest = car_refuelings[0]
                previous = car_refuelings[1]
                distance = latest.odomSnapshot.mileage - previous.odomSnapshot.mileage
                mpg = (distance / latest.amount) if latest.amount else None
                forecast[car.id] = {
                    "distance_between_last_refuels": distance,
                    "latest_fuel_amount": latest.amount,
                    "estimated_consumption_mpg": mpg,
                    "latest_refuel_at": latest.odomSnapshot.date,
                }
            else:
                forecast[car.id] = None

        return {
            "components": components,
            "maintenance_schedules": dict(schedules_by_car),
            "replacements": dict(replacements_by_car),
            "defect_reports": defects,
            "repair_actions": repair_actions,
            "work_orders": work_orders,
            "requirements": requirement_links,
            "fuel_forecast": forecast,
            "traceability_note": "Lifecycle module now tracks serialized components, work orders, defects, schedules, and replacements in dedicated models.",
        }


class ProfileScreen(mixins.LoginRequiredMixin, generic.DetailView):
    model = User
    context_object_name = "user_object"

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)


class UserDelete(mixins.LoginRequiredMixin, generic.DeleteView):
    model = User
    success_url = "/"

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)


class Settings(mixins.LoginRequiredMixin, views.View):
    def get(self, request):
        form = SettingsForm(
            initial={"email_notifications": request.user.email_notifications}
        )
        return render(request, "autodo/settings.html", {"form": form})

    def post(self, request):
        form = SettingsForm(request.POST)
        if form.is_valid():
            request.user.email_notifications = form.cleaned_data["email_notifications"]
            request.user.save()
            return HttpResponseRedirect("/settings")
        return render(request, "autodo/settings.html", {"form": form})
