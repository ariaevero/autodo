import sys

from django import forms
from django.forms.models import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from extra_views import InlineFormSetFactory
from djmoney.forms.fields import MoneyField, MoneyWidget
from djmoney.settings import CURRENCY_CHOICES

from autodo.models import (
    Car,
    OdomSnapshot,
    User,
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

default_form_classes = [
    "bg-gray-50",
    "dark:bg-background_med",
    "my-2",
    "py-1",
    "px-4",
    "border",
    "border-gray-400",
    "dark:border-gray-800",
    "rounded",
    "focus:outline-none",
    "focus:border-blue-500",
    "placeholder-gray-500",
    "dark:placeholder-gray-300",
    "w-full"
]
default_form_class = " ".join(default_form_classes)


class AddCarForm(forms.ModelForm):
    # def clean_year(self):
    #   return self.cleaned_data['year']

    class Meta:
        model = Car
        exclude = ["owner"]
        widgets = {
            "name": forms.TextInput(attrs={"class": default_form_class}),
            "make": forms.TextInput(attrs={"class": default_form_class}),
            "model": forms.TextInput(attrs={"class": default_form_class}),
            "year": forms.NumberInput(attrs={"class": default_form_class}),
            "plate": forms.TextInput(attrs={"class": default_form_class}),
            "vin": forms.TextInput(attrs={"class": default_form_class}),
            "color": forms.TextInput(
                attrs={
                    "type": "color",
                    "class": "bg-gray-50 dark:bg-background_med w-12 my-2 py-1 px-4 border border-gray-400 dark:border-gray-800 rounded focus:outline-none focus:border-blue-500 placeholder-gray-500",
                }
            ),
        }


class AddOdomSnapshotForm(forms.ModelForm):
    """Use this to create a refueling because the foreign key needs to point in this direction."""

    class Meta:
        model = OdomSnapshot
        exclude = ["owner"]
        widgets = {
            "car": forms.Select(attrs={"class": default_form_class, "required": True}),
            "date": forms.DateInput(
                attrs={"class": default_form_class, "type": "date"}
            ),
            "mileage": forms.NumberInput(
                attrs={"class": default_form_class, "inputmode": "decimal"}
            ),
        }


class CompletionOdomSnapshotForm(forms.ModelForm):
    """Use this to modify a Todo's completion info"""

    class Meta:
        model = OdomSnapshot
        exclude = ["owner", "car"]
        labels = {"mileage": "Completion Mileage", "date": "Completion Date"}
        widgets = {
            "date": forms.DateInput(
                attrs={"class": default_form_class, "type": "date"}
            ),
            "mileage": forms.NumberInput(
                attrs={"class": default_form_class, "inputmode": "decimal"}
            ),
        }


class OdomMileageOnlyFormset(InlineFormSetFactory):
    model = OdomSnapshot
    fields = ["mileage"]
    factory_kwargs = {
        "extra": 1,
        "can_delete": False,
        "widgets": {
            "mileage": forms.NumberInput(
                attrs={
                    "class": default_form_class,
                    "required": True,
                    "inputmode": "decimal",
                }
            ),
        },
    }


class RefuelingForm(forms.ModelForm):
    """Use this to create a refueling because the foreign key needs to point in this direction."""

    cost = MoneyField(
        widget=MoneyWidget(
            amount_widget=forms.TextInput(
                attrs={
                    "class": " ".join(
                        [
                            "bg-gray-50",
                            "dark:bg-background_med",
                            "my-2",
                            "py-1",
                            "px-4",
                            "border",
                            "border-gray-400",
                            "dark:border-gray-800",
                            "rounded",
                            "focus:outline-none",
                            "focus:border-blue-500",
                            "placeholder-gray-500",
                            "dark:placeholder-gray-300",
                            "w-7/12",
                        ]
                    ),
                    "inputmode": "decimal",
                }
            ),
            currency_widget=forms.Select(
                choices=CURRENCY_CHOICES,
                attrs={
                    "class": " ".join(
                        [
                            "bg-gray-50",
                            "dark:bg-background_med",
                            "my-2",
                            "py-1",
                            "px-4",
                            "border",
                            "border-gray-400",
                            "dark:border-gray-800",
                            "rounded",
                            "focus:outline-none",
                            "focus:border-blue-500",
                            "placeholder-gray-500",
                            "dark:placeholder-gray-300",
                            "w-5/12",
                        ]
                    ),
                },
            ),
        )
    )

    class Meta:
        model = Refueling
        fields = ["cost", "amount"]
        widgets = {
            "amount": forms.NumberInput(
                attrs={"class": default_form_class, "inputmode": "decimal"}
            ),
        }


RefuelingCreateFormset = inlineformset_factory(
    OdomSnapshot,
    Refueling,
    fields=("cost", "amount"),
    widgets={
        "cost": forms.NumberInput(
            attrs={
                "class": default_form_class,
                "required": True,
                "inputmode": "decimal",
            }
        ),
        "amount": forms.NumberInput(
            attrs={
                "class": default_form_class,
                "required": True,
                "inputmode": "decimal",
            }
        ),
    },
    extra=1,
    can_delete=False,
)


class AddTodoForm(forms.ModelForm):
    repeat_num = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={"class": default_form_class, "inputmode": "decimal"}
        ),
    )
    repeat_choice = forms.ChoiceField(
        choices=[
            ("DAY", "Days"),
            ("WEEK", "Weeks"),
            ("MNTH", "Months"),
            ("YEAR", "Years"),
            ("MILE", "Miles"),
        ],
        widget=forms.Select(attrs={"class": default_form_class}),
    )
    # set the default to repeat forever
    field_order = [
        "car",
        "name",
        "dueMileage",
        "dueDate",
        "notes",
        "repeat_num",
        "repeat_choice",
        "complete",
    ]

    def save(self, commit=True):
        t = super().save(commit=False)
        if self.cleaned_data["repeat_num"] != 0:
            if self.cleaned_data["repeat_choice"] == "MILE":
                t.mileageRepeatInterval = self.cleaned_data["repeat_num"]
            elif self.cleaned_data["repeat_choice"] == "DAY":
                t.daysRepeatInterval = self.cleaned_data["repeat_num"]
            elif self.cleaned_data["repeat_choice"] == "WEEK":
                t.daysRepeatInterval = self.cleaned_data["repeat_num"] * 7
            elif self.cleaned_data["repeat_choice"] == "MNTH":
                t.monthsRepeatInterval = self.cleaned_data["repeat_num"]
            else:
                t.yearsRepeatInterval = self.cleaned_data["repeat_num"]
        return super().save(commit)

    class Meta:
        model = Todo
        fields = [
            "car",
            "name",
            "dueMileage",
            "dueDate",
            "notes",
            "complete",
        ]

        widgets = {
            "car": forms.Select(attrs={"class": default_form_class, "required": True}),
            "name": forms.TextInput(attrs={"class": default_form_class}),
            "complete": forms.CheckboxInput(
                attrs={
                    "class": " ".join(
                        [
                            "bg-gray-50",
                            "dark:bg-background_light",
                            "my-auto",
                            "mx-0",
                            "ml-auto",
                            "p-3",
                            "right-0",
                            "border",
                            "border-gray-400",
                            "dark:border-gray-700",
                            "rounded",
                            "focus:ring-transparent",
                            "focus:border-blue-500",
                        ]
                    )
                }
            ),
            "dueMileage": forms.NumberInput(attrs={"class": default_form_class}),
            "dueDate": forms.DateInput(
                attrs={"class": default_form_class, "type": "date"}
            ),
            "notes": forms.Textarea(attrs={"class": default_form_class + " h-24"}),
        }


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")


class SettingsForm(forms.Form):
    email_notifications = forms.BooleanField(
        label="Receive notifications about Todos",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": " ".join(
                    [
                        "bg-gray-50",
                        "dark:bg-background_light",
                        "my-auto",
                        "mx-0",
                        "ml-auto",
                        "p-3",
                        "right-0",
                        "border",
                        "border-gray-400",
                        "dark:border-gray-700",
                        "rounded",
                        "focus:ring-transparent",
                        "focus:border-blue-500",
                    ]
                )
            }
        ),
    )


class AssetComponentForm(forms.ModelForm):
    class Meta:
        model = AssetComponent
        exclude = ["owner"]
        widgets = {
            "car": forms.Select(attrs={"class": default_form_class}),
            "name": forms.TextInput(attrs={"class": default_form_class}),
            "serial_number": forms.TextInput(attrs={"class": default_form_class}),
            "manufacturer": forms.TextInput(attrs={"class": default_form_class}),
            "installed_at": forms.DateInput(attrs={"class": default_form_class, "type": "date"}),
            "removed_at": forms.DateInput(attrs={"class": default_form_class, "type": "date"}),
            "lifecycle_status": forms.Select(attrs={"class": default_form_class}),
            "notes": forms.Textarea(attrs={"class": default_form_class}),
        }


class MaintenanceScheduleForm(forms.ModelForm):
    class Meta:
        model = MaintenanceSchedule
        exclude = ["owner"]
        widgets = {
            "car": forms.Select(attrs={"class": default_form_class}),
            "component": forms.Select(attrs={"class": default_form_class}),
            "title": forms.TextInput(attrs={"class": default_form_class}),
            "description": forms.Textarea(attrs={"class": default_form_class}),
            "interval_days": forms.NumberInput(attrs={"class": default_form_class, "inputmode": "numeric"}),
            "interval_mileage": forms.NumberInput(attrs={"class": default_form_class, "inputmode": "decimal"}),
            "next_due_date": forms.DateInput(attrs={"class": default_form_class, "type": "date"}),
            "next_due_mileage": forms.NumberInput(attrs={"class": default_form_class, "inputmode": "decimal"}),
        }


class DefectReportForm(forms.ModelForm):
    class Meta:
        model = DefectReport
        exclude = ["owner"]
        widgets = {
            "car": forms.Select(attrs={"class": default_form_class}),
            "component": forms.Select(attrs={"class": default_form_class}),
            "reported_by": forms.Select(attrs={"class": default_form_class}),
            "title": forms.TextInput(attrs={"class": default_form_class}),
            "description": forms.Textarea(attrs={"class": default_form_class}),
            "severity": forms.Select(attrs={"class": default_form_class}),
            "status": forms.Select(attrs={"class": default_form_class}),
            "detected_at": forms.DateInput(attrs={"class": default_form_class, "type": "date"}),
            "resolved_at": forms.DateInput(attrs={"class": default_form_class, "type": "date"}),
            "root_cause": forms.Textarea(attrs={"class": default_form_class}),
            "corrective_action": forms.Textarea(attrs={"class": default_form_class}),
            "preventive_action": forms.Textarea(attrs={"class": default_form_class}),
        }


class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        exclude = ["owner"]
        widgets = {
            "car": forms.Select(attrs={"class": default_form_class}),
            "component": forms.Select(attrs={"class": default_form_class}),
            "schedule": forms.Select(attrs={"class": default_form_class}),
            "defect_report": forms.Select(attrs={"class": default_form_class}),
            "title": forms.TextInput(attrs={"class": default_form_class}),
            "description": forms.Textarea(attrs={"class": default_form_class}),
            "status": forms.Select(attrs={"class": default_form_class}),
            "priority": forms.Select(attrs={"class": default_form_class}),
            "opened_at": forms.DateInput(attrs={"class": default_form_class, "type": "date"}),
            "due_at": forms.DateInput(attrs={"class": default_form_class, "type": "date"}),
            "completed_at": forms.DateInput(attrs={"class": default_form_class, "type": "date"}),
            "assigned_to": forms.Select(attrs={"class": default_form_class}),
            "created_by": forms.Select(attrs={"class": default_form_class}),
        }


class PartReplacementForm(forms.ModelForm):
    class Meta:
        model = PartReplacement
        exclude = ["owner"]
        widgets = {
            "work_order": forms.Select(attrs={"class": default_form_class}),
            "car": forms.Select(attrs={"class": default_form_class}),
            "component": forms.Select(attrs={"class": default_form_class}),
            "part_name": forms.TextInput(attrs={"class": default_form_class}),
            "part_serial_number": forms.TextInput(attrs={"class": default_form_class}),
            "replaced_at": forms.DateInput(attrs={"class": default_form_class, "type": "date"}),
            "odometer_mileage": forms.NumberInput(attrs={"class": default_form_class, "inputmode": "decimal"}),
            "supplier": forms.TextInput(attrs={"class": default_form_class}),
            "cost_amount": forms.NumberInput(attrs={"class": default_form_class, "inputmode": "decimal"}),
        }
