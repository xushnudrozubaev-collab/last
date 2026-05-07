from django.urls import path

from .views import (
    DashboardView,
    MatchCreateView,
    MatchDetailView,
    MatchListView,
    MatchUpdateView,
    PlayerCreateView,
    PlayerDeleteView,
    PlayerDetailView,
    PlayerListView,
    PlayerUpdateView,
    SettingsView,
    StatisticsView,
    TrainingCreateView,
    TrainingDeleteView,
    TrainingListView,
    TrainingUpdateView,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("players/", PlayerListView.as_view(), name="player_list"),
    path("players/add/", PlayerCreateView.as_view(), name="player_add"),
    path("players/<int:pk>/", PlayerDetailView.as_view(), name="player_detail"),
    path("players/<int:pk>/edit/", PlayerUpdateView.as_view(), name="player_edit"),
    path("players/<int:pk>/delete/", PlayerDeleteView.as_view(), name="player_delete"),
    path("matches/", MatchListView.as_view(), name="match_list"),
    path("matches/add/", MatchCreateView.as_view(), name="match_add"),
    path("matches/<int:pk>/", MatchDetailView.as_view(), name="match_detail"),
    path("matches/<int:pk>/edit/", MatchUpdateView.as_view(), name="match_edit"),
    path("training/", TrainingListView.as_view(), name="training_list"),
    path("training/add/", TrainingCreateView.as_view(), name="training_add"),
    path("training/<int:pk>/edit/", TrainingUpdateView.as_view(), name="training_edit"),
    path("training/<int:pk>/delete/", TrainingDeleteView.as_view(), name="training_delete"),
    path("statistics/", StatisticsView.as_view(), name="statistics"),
    path("settings/", SettingsView.as_view(), name="settings"),
]
