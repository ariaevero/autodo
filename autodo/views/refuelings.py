from django.contrib.auth import mixins
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.core.serializers import serialize
from django.utils import timezone
from djmoney.money import Money
from shapeshifter.views import MultiModelFormView

from autodo.models import Car, OdomSnapshot, Refueling, FuelPriceConfig
from autodo.forms import AddOdomSnapshotForm, RefuelingForm, RefuelingCreateFormset


def get_admin_locked_refueling_values(user, car):
    latest = (
        Refueling.objects.filter(owner=user, odomSnapshot__car=car)
        .order_by("-odomSnapshot__date")
        .first()
    )
    price_config = FuelPriceConfig.objects.filter(fuel_type=car.fuel_type).first()
    price_per_litre = price_config.price_per_litre if price_config else Money(0, "USD")

    amount = latest.amount if latest else 0
    cost = Money(price_per_litre.amount * amount, price_per_litre.currency)
    return cost, amount


class RefuelingListView(mixins.LoginRequiredMixin, generic.ListView):
    model = Refueling

    def get_queryset(self):
        return Refueling.objects.filter(owner=self.request.user).order_by(
            "-odomSnapshot__date"
        )


class RefuelingDetailView(mixins.LoginRequiredMixin, generic.DetailView):
    model = Refueling


class RefuelingCreate(mixins.LoginRequiredMixin, MultiModelFormView):
    form_classes = (AddOdomSnapshotForm, RefuelingForm)
    template_name = "autodo/odomsnapshot_form.html"
    initial = {"addodomsnapshotform": {"date": timezone.now()}}
    success_url = reverse_lazy("refuelings")

    def get_forms(self):
        # override the form class instantiation to specify the car queryset
        form = AddOdomSnapshotForm(**self.get_form_kwargs(AddOdomSnapshotForm))
        form.fields["car"].queryset = Car.objects.filter(owner=self.request.user)
        refueling_form = RefuelingForm(**self.get_form_kwargs(RefuelingForm))
        if not self.request.user.can_manage_fuel_rates:
            refueling_form.fields["cost"].disabled = True
            refueling_form.fields["amount"].disabled = True
            form.fields["mileage"].disabled = True
        return {
            "addodomsnapshotform": form,
            "refuelingform": refueling_form,
        }

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        snaps = OdomSnapshot.objects.filter(owner=self.request.user)
        cars = Car.objects.filter(owner=self.request.user)
        data["cars"] = serialize("json", cars)
        data["snaps"] = serialize("json", snaps)
        if self.request.POST:
            data["refueling"] = RefuelingCreateFormset(self.request.POST)
        else:
            data["refueling"] = RefuelingCreateFormset()
        return data

    def forms_valid(self):
        forms = self.get_forms()
        snapshot_form = forms["addodomsnapshotform"]
        refueling_form = forms["refuelingform"]

        s = snapshot_form.save(commit=False)
        s.owner = self.request.user

        if not self.request.user.can_manage_fuel_rates:
            latest_snap = (
                OdomSnapshot.objects.filter(owner=self.request.user, car=s.car)
                .order_by("-mileage")
                .first()
            )
            if latest_snap:
                s.mileage = latest_snap.mileage
        s.save()

        r = refueling_form.save(commit=False)
        r.owner = self.request.user
        r.odomSnapshot = s
        if not self.request.user.can_manage_fuel_rates:
            locked_cost, locked_amount = get_admin_locked_refueling_values(
                self.request.user, s.car
            )
            r.cost = locked_cost
            r.amount = locked_amount
        r.save()

        return HttpResponseRedirect(self.success_url)


class RefuelingUpdate(mixins.LoginRequiredMixin, MultiModelFormView):
    form_classes = (AddOdomSnapshotForm, RefuelingForm)
    template_name = "autodo/odomsnapshot_form.html"
    success_url = reverse_lazy("refuelings")

    def get_forms(self):
        # override the form class instantiation to specify the car queryset
        form = AddOdomSnapshotForm(**self.get_form_kwargs(AddOdomSnapshotForm))
        form.fields["car"].queryset = Car.objects.filter(owner=self.request.user)
        refueling_form = RefuelingForm(**self.get_form_kwargs(RefuelingForm))
        if not self.request.user.can_manage_fuel_rates:
            refueling_form.fields["cost"].disabled = True
            refueling_form.fields["amount"].disabled = True
            form.fields["mileage"].disabled = True
        return {
            "addodomsnapshotform": form,
            "refuelingform": refueling_form,
        }

    def forms_valid(self):
        forms = self.get_forms()
        snapshot_form = forms["addodomsnapshotform"]
        refueling_form = forms["refuelingform"]

        s = snapshot_form.save(commit=False)
        s.owner = self.request.user

        if not self.request.user.can_manage_fuel_rates:
            latest_snap = (
                OdomSnapshot.objects.filter(owner=self.request.user, car=s.car)
                .exclude(pk=s.pk)
                .order_by("-mileage")
                .first()
            )
            if latest_snap:
                s.mileage = latest_snap.mileage
        s.save()

        r = refueling_form.save(commit=False)
        r.owner = self.request.user
        r.odomSnapshot = s
        if not self.request.user.can_manage_fuel_rates:
            locked_cost, locked_amount = get_admin_locked_refueling_values(
                self.request.user, s.car
            )
            r.cost = locked_cost
            r.amount = locked_amount
        r.save()

        return HttpResponseRedirect(self.success_url)

    def get_instances(self):
        r = Refueling.objects.get(pk=self.kwargs["pk"])
        snap = OdomSnapshot.objects.get(pk=r.odomSnapshot.id)

        instances = {
            "addodomsnapshotform": snap,
            "refuelingform": r,
        }
        return instances


class OdomSnapshotDelete(mixins.LoginRequiredMixin, generic.DeleteView):
    model = OdomSnapshot
    success_url = reverse_lazy("refuelings")
