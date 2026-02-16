from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views

from autodo.views.cars import (
    CarListView,
    CarDetailView,
    CarCreate,
    CarUpdate,
    CarDelete,
)
from autodo.views.refuelings import (
    RefuelingListView,
    RefuelingDetailView,
    RefuelingCreate,
    RefuelingUpdate,
    OdomSnapshotDelete,
)
from autodo.views.views import (
    Stats,
    landing_page,
    register,
    ProfileScreen,
    UserDelete,
    Settings,
)
from autodo.views.todos import (
    TodoListView,
    TodoDetailView,
    TodoCreate,
    TodoUpdate,
    TodoDelete,
    todoComplete,
)

from autodo.views.lifecycle import (
    LifecycleDashboardView,
    AssetComponentListView,
    AssetComponentCreateView,
    MaintenanceScheduleListView,
    MaintenanceScheduleCreateView,
    DefectReportListView,
    DefectReportCreateView,
    WorkOrderListView,
    WorkOrderCreateView,
    PartReplacementListView,
    PartReplacementCreateView,
)

from autodo.views.stats import (
    fuelEfficiencyStats,
    fuelUsageByCarStats,
    drivingRateStats,
    fuelUsageByMonthStats,
    completedTodosStats,
    refuelingsLoggedStats,
)

urlpatterns = [
    path("", landing_page),
    # override the login view to redirect if the user is logged in
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(redirect_authenticated_user=True),
        name="login",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/register/", register, name="register"),
    path("accounts/profile/<int:pk>/", ProfileScreen.as_view(), name="profile"),
    path(
        "accounts/profile/<int:pk>/delete",
        UserDelete.as_view(),
        name="user_confirm_delete",
    ),
    path("cars/", CarListView.as_view(), name="cars"),
    path("cars/create/", CarCreate.as_view(), name="cars/create"),
    path("cars/<int:pk>/", CarDetailView.as_view(), name="cars/detail"),
    path("cars/<int:pk>/update/", CarUpdate.as_view(), name="cars/update"),
    path("cars/<int:pk>/delete/", CarDelete.as_view(), name="cars/delete"),
    path("refuelings/", RefuelingListView.as_view(), name="refuelings"),
    path("refuelings/create/", RefuelingCreate.as_view(), name="refuelings/create"),
    path(
        "refuelings/<int:pk>/", RefuelingDetailView.as_view(), name="refuelings/detail"
    ),
    path(
        "refuelings/<int:pk>/update/",
        RefuelingUpdate.as_view(),
        name="refuelings/update",
    ),
    # Using the parent delete view here to get both parent and child
    path(
        "refuelings/<int:pk>/delete/",
        OdomSnapshotDelete.as_view(),
        name="refuelings/delete",
    ),
    path("home/", TodoListView.as_view(), name="home"),
    path("todos/create/", TodoCreate.as_view(), name="todos/create"),
    path("todos/<int:pk>/", TodoDetailView.as_view(), name="todos/detail"),
    path("todos/<int:pk>/update/", TodoUpdate.as_view(), name="todos/update"),
    path("todos/<int:pk>/delete/", TodoDelete.as_view(), name="todos/delete"),
    path("api/todos/<int:pk>/", todoComplete, name="api_update_todo"),
    path("stats/", Stats.as_view(), name="stats"),
    path("stats/fuelEfficiency", fuelEfficiencyStats, name="stats/fuelEfficiency"),
    path(
        "stats/fuelUsageByCar",
        fuelUsageByCarStats,
        name="stats/fuelUsageByCar",
    ),
    path("stats/drivingRate", drivingRateStats, name="stats/drivingRate"),
    path(
        "stats/fuelUsageByMonth", fuelUsageByMonthStats, name="stats/fuelUsageByMonth"
    ),
    path("stats/completedTodos", completedTodosStats, name="stats/completedTodos"),
    path(
        "stats/refuelingsLogged", refuelingsLoggedStats, name="stats/refuelingsLogged"
    ),
    path("lifecycle/", LifecycleDashboardView.as_view(), name="lifecycle"),
    path("lifecycle/components/", AssetComponentListView.as_view(), name="lifecycle/components"),
    path("lifecycle/components/create/", AssetComponentCreateView.as_view(), name="lifecycle/components/create"),
    path("lifecycle/schedules/", MaintenanceScheduleListView.as_view(), name="lifecycle/schedules"),
    path("lifecycle/schedules/create/", MaintenanceScheduleCreateView.as_view(), name="lifecycle/schedules/create"),
    path("lifecycle/defects/", DefectReportListView.as_view(), name="lifecycle/defects"),
    path("lifecycle/defects/create/", DefectReportCreateView.as_view(), name="lifecycle/defects/create"),
    path("lifecycle/workorders/", WorkOrderListView.as_view(), name="lifecycle/workorders"),
    path("lifecycle/workorders/create/", WorkOrderCreateView.as_view(), name="lifecycle/workorders/create"),
    path("lifecycle/replacements/", PartReplacementListView.as_view(), name="lifecycle/replacements"),
    path("lifecycle/replacements/create/", PartReplacementCreateView.as_view(), name="lifecycle/replacements/create"),
    path("settings/", Settings.as_view(), name="settings"),
]
