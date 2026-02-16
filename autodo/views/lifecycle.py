from django.contrib.auth import mixins
from django.urls import reverse_lazy
from django.views import generic

from autodo.models import (
    AssetComponent,
    DefectReport,
    MaintenanceSchedule,
    PartReplacement,
    WorkOrder,
)
from autodo.forms import (
    AssetComponentForm,
    DefectReportForm,
    MaintenanceScheduleForm,
    PartReplacementForm,
    WorkOrderForm,
)


class OwnerScopedQuerysetMixin(mixins.LoginRequiredMixin):
    owner_field = "owner"

    def get_queryset(self):
        return self.model.objects.filter(**{self.owner_field: self.request.user})


class OwnerScopedCreateMixin(mixins.LoginRequiredMixin):
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class LifecycleDashboardView(mixins.LoginRequiredMixin, generic.TemplateView):
    template_name = "autodo/lifecycle_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        owner = self.request.user
        components = AssetComponent.objects.filter(owner=owner)
        schedules = MaintenanceSchedule.objects.filter(owner=owner, active=True)
        work_orders = WorkOrder.objects.filter(owner=owner)
        defects = DefectReport.objects.filter(owner=owner)
        replacements = PartReplacement.objects.filter(owner=owner)

        context.update(
            {
                "component_count": components.count(),
                "active_schedule_count": schedules.count(),
                "open_work_order_count": work_orders.exclude(
                    status__in=[WorkOrder.Status.COMPLETED, WorkOrder.Status.CLOSED]
                ).count(),
                "open_defect_count": defects.exclude(
                    status__in=[DefectReport.Status.RESOLVED, DefectReport.Status.CLOSED]
                ).count(),
                "replacement_count": replacements.count(),
                "recent_work_orders": work_orders.order_by("-opened_at")[:10],
                "recent_defects": defects.order_by("-detected_at")[:10],
                "recent_replacements": replacements.order_by("-replaced_at")[:10],
            }
        )
        return context


class AssetComponentListView(OwnerScopedQuerysetMixin, generic.ListView):
    model = AssetComponent
    template_name = "autodo/component_list.html"


class AssetComponentCreateView(OwnerScopedCreateMixin, generic.CreateView):
    form_class = AssetComponentForm
    template_name = "autodo/lifecycle_form.html"
    success_url = reverse_lazy("lifecycle/components")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["car"].queryset = form.fields["car"].queryset.filter(
            owner=self.request.user
        )
        return form


class MaintenanceScheduleListView(OwnerScopedQuerysetMixin, generic.ListView):
    model = MaintenanceSchedule
    template_name = "autodo/schedule_list.html"


class MaintenanceScheduleCreateView(OwnerScopedCreateMixin, generic.CreateView):
    form_class = MaintenanceScheduleForm
    template_name = "autodo/lifecycle_form.html"
    success_url = reverse_lazy("lifecycle/schedules")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["car"].queryset = form.fields["car"].queryset.filter(
            owner=self.request.user
        )
        form.fields["component"].queryset = form.fields["component"].queryset.filter(
            owner=self.request.user
        )
        return form


class DefectReportListView(OwnerScopedQuerysetMixin, generic.ListView):
    model = DefectReport
    template_name = "autodo/defect_list.html"


class DefectReportCreateView(OwnerScopedCreateMixin, generic.CreateView):
    form_class = DefectReportForm
    template_name = "autodo/lifecycle_form.html"
    success_url = reverse_lazy("lifecycle/defects")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["car"].queryset = form.fields["car"].queryset.filter(
            owner=self.request.user
        )
        form.fields["component"].queryset = form.fields["component"].queryset.filter(
            owner=self.request.user
        )
        form.fields["reported_by"].queryset = form.fields["reported_by"].queryset.filter(
            pk=self.request.user.pk
        )
        return form


class WorkOrderListView(OwnerScopedQuerysetMixin, generic.ListView):
    model = WorkOrder
    template_name = "autodo/workorder_list.html"


class WorkOrderCreateView(OwnerScopedCreateMixin, generic.CreateView):
    form_class = WorkOrderForm
    template_name = "autodo/lifecycle_form.html"
    success_url = reverse_lazy("lifecycle/workorders")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["car"].queryset = form.fields["car"].queryset.filter(
            owner=self.request.user
        )
        form.fields["component"].queryset = form.fields["component"].queryset.filter(
            owner=self.request.user
        )
        form.fields["schedule"].queryset = form.fields["schedule"].queryset.filter(
            owner=self.request.user
        )
        form.fields["defect_report"].queryset = form.fields["defect_report"].queryset.filter(
            owner=self.request.user
        )
        form.fields["assigned_to"].queryset = form.fields["assigned_to"].queryset.filter(
            pk=self.request.user.pk
        )
        form.fields["created_by"].queryset = form.fields["created_by"].queryset.filter(
            pk=self.request.user.pk
        )
        return form


class PartReplacementListView(OwnerScopedQuerysetMixin, generic.ListView):
    model = PartReplacement
    template_name = "autodo/replacement_list.html"


class PartReplacementCreateView(OwnerScopedCreateMixin, generic.CreateView):
    form_class = PartReplacementForm
    template_name = "autodo/lifecycle_form.html"
    success_url = reverse_lazy("lifecycle/replacements")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["car"].queryset = form.fields["car"].queryset.filter(
            owner=self.request.user
        )
        form.fields["component"].queryset = form.fields["component"].queryset.filter(
            owner=self.request.user
        )
        form.fields["work_order"].queryset = form.fields["work_order"].queryset.filter(
            owner=self.request.user
        )
        return form
