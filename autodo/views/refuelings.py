from statistics import mean

from django.contrib.auth import mixins
from django.views import generic
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.core.serializers import serialize
from django.utils import timezone
from shapeshifter.views import MultiModelFormView

from autodo.models import Car, OdomSnapshot, Refueling
from autodo.forms import AddOdomSnapshotForm, RefuelingForm, RefuelingCreateFormset


class RefuelingListView(mixins.LoginRequiredMixin, generic.ListView):
    model = Refueling

    def get_queryset(self):
        return Refueling.objects.filter(owner=self.request.user).order_by(
            "-odomSnapshot__date"
        )


class RefuelingDetailView(mixins.LoginRequiredMixin, generic.DetailView):
    model = Refueling

    def get_queryset(self):
        return Refueling.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["fuel_analysis"] = self._build_fuel_analysis(self.object)
        return data

    def _build_fuel_analysis(self, refueling):
        car_refuelings = (
            Refueling.objects.filter(
                owner=self.request.user,
                odomSnapshot__car=refueling.odomSnapshot.car,
            )
            .select_related("odomSnapshot")
            .order_by("odomSnapshot__date")
        )

        previous_refueling = (
            car_refuelings.filter(odomSnapshot__date__lt=refueling.odomSnapshot.date)
            .order_by("-odomSnapshot__date")
            .first()
        )
        next_refueling = (
            car_refuelings.filter(odomSnapshot__date__gt=refueling.odomSnapshot.date)
            .order_by("odomSnapshot__date")
            .first()
        )

        mpg_samples = []
        ordered = list(car_refuelings)
        for idx in range(1, len(ordered)):
            previous = ordered[idx - 1]
            current = ordered[idx]
            distance = current.odomSnapshot.mileage - previous.odomSnapshot.mileage
            if distance > 0 and current.amount > 0:
                mpg_samples.append(distance / current.amount)

        current_leg_mpg = None
        distance_since_last = None
        if previous_refueling:
            distance_since_last = (
                refueling.odomSnapshot.mileage - previous_refueling.odomSnapshot.mileage
            )
            if distance_since_last > 0 and refueling.amount > 0:
                current_leg_mpg = distance_since_last / refueling.amount

        average_mpg = mean(mpg_samples) if mpg_samples else None

        anomaly = None
        if current_leg_mpg and average_mpg and average_mpg > 0:
            deviation = abs(current_leg_mpg - average_mpg) / average_mpg
            if deviation >= 0.2:
                anomaly = {
                    "type": "fuel_efficiency",
                    "message": "Fuel efficiency deviates by at least 20% from this vehicle's average.",
                    "deviation_ratio": deviation,
                }

        return {
            "previous_refueling": previous_refueling,
            "next_refueling": next_refueling,
            "distance_since_last": distance_since_last,
            "current_leg_mpg": current_leg_mpg,
            "average_mpg": average_mpg,
            "estimated_next_refuel_miles": (
                refueling.odomSnapshot.mileage + (average_mpg * refueling.amount)
                if average_mpg and refueling.amount
                else None
            ),
            "anomaly": anomaly,
            "purchase_recorded_at": refueling.odomSnapshot.date,
        }


class RefuelingCreate(mixins.LoginRequiredMixin, MultiModelFormView):
    form_classes = (AddOdomSnapshotForm, RefuelingForm)
    template_name = "autodo/odomsnapshot_form.html"
    initial = {"addodomsnapshotform": {"date": timezone.now()}}
    success_url = reverse_lazy("refuelings")

    def get_forms(self):
        # override the form class instantiation to specify the car queryset
        form = AddOdomSnapshotForm(**self.get_form_kwargs(AddOdomSnapshotForm))
        form.fields["car"].queryset = Car.objects.filter(owner=self.request.user)
        return {
            "addodomsnapshotform": form,
            "refuelingform": RefuelingForm(**self.get_form_kwargs(RefuelingForm)),
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
        s.save()

        r = refueling_form.save(commit=False)
        r.owner = self.request.user
        r.odomSnapshot = s
        r.save()

        return HttpResponseRedirect(self.success_url)


class RefuelingUpdate(mixins.LoginRequiredMixin, MultiModelFormView):
    form_classes = (AddOdomSnapshotForm, RefuelingForm)
    template_name = "autodo/odomsnapshot_form.html"
    success_url = reverse_lazy("refuelings")

    def get_queryset(self):
        return Refueling.objects.filter(owner=self.request.user)

    def get_forms(self):
        # override the form class instantiation to specify the car queryset
        form = AddOdomSnapshotForm(**self.get_form_kwargs(AddOdomSnapshotForm))
        form.fields["car"].queryset = Car.objects.filter(owner=self.request.user)
        return {
            "addodomsnapshotform": form,
            "refuelingform": RefuelingForm(**self.get_form_kwargs(RefuelingForm)),
        }

    def get_instances(self):
        r = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        snap = get_object_or_404(
            OdomSnapshot,
            pk=r.odomSnapshot.id,
            owner=self.request.user,
        )

        instances = {
            "addodomsnapshotform": snap,
            "refuelingform": r,
        }
        return instances


class OdomSnapshotDelete(mixins.LoginRequiredMixin, generic.DeleteView):
    model = OdomSnapshot
    success_url = reverse_lazy("refuelings")

    def get_queryset(self):
        return OdomSnapshot.objects.filter(owner=self.request.user)
