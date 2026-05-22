from django.contrib import admin

from .models import (
    CoachProfile,
    Match,
    Player,
    PlayerStatistic,
    TeamStatistic,
    Training,
    TrainingAttendance,
    UserProfile,
)


@admin.register(CoachProfile)
class CoachProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "club_name", "role", "experience_years")
    search_fields = ("full_name", "club_name", "role")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "language", "theme", "phone")
    list_filter = ("language", "theme", "email_notifications", "sms_notifications", "system_alerts")
    search_fields = ("user__username", "user__email", "phone")


class PlayerStatisticInline(admin.StackedInline):
    model = PlayerStatistic
    extra = 0


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "shirt_number", "position", "age", "nationality")
    list_filter = ("position", "nationality")
    search_fields = ("full_name", "nationality")
    inlines = [PlayerStatisticInline]


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ("title", "training_type", "training_date", "start_time", "location")
    list_filter = ("training_type", "training_date")
    search_fields = ("title", "location")


@admin.register(TrainingAttendance)
class TrainingAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "training",
        "player",
        "attendance_status",
        "physical_condition",
        "activity_level",
        "discipline",
        "rating",
        "attended_minutes",
        "training_duration_minutes",
        "fatigue_level",
        "pain_level",
        "sleep_quality",
        "activity_score",
        "heart_rate",
        "blood_pressure",
        "body_temperature",
        "oxygen_saturation",
        "injury_status",
    )
    list_filter = (
        "attendance_status",
        "physical_condition",
        "activity_level",
        "discipline",
        "injury_status",
        "training__training_date",
    )
    search_fields = ("training__title", "player__full_name", "coach_note")


@admin.register(TeamStatistic)
class TeamStatisticAdmin(admin.ModelAdmin):
    list_display = ("title", "metric_value", "accent", "sort_order")
    list_editable = ("sort_order",)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("home_team", "away_team", "match_date", "match_time", "status", "result_label")
    list_filter = ("status", "match_date")
    search_fields = ("home_team", "away_team", "stadium")
