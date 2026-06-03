from django.contrib import admin

from .models import (
    AIConversation,
    AIMessage,
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


class AIMessageInline(admin.TabularInline):
    model = AIMessage
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("role", "content", "created_at")


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_active", "get_message_count", "created_at")
    list_filter = ("is_active", "created_at", "user")
    search_fields = ("title", "user__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = [AIMessageInline]

    def get_message_count(self, obj):
        return obj.messages.count()
    get_message_count.short_description = "Xabarlar soni"


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "content_preview", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("content", "conversation__title")
    readonly_fields = ("created_at",)

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = "Xabar"
