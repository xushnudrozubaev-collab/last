from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .attendance import ACTIVE_STATUSES, calculate_player_attendance_stats, get_training_duration_minutes
from .models import (
    AIConversation,
    AIMessage,
    CoachProfile,
    Match,
    Player,
    PlayerStatistic,
    PROJECT_CLUB_NAME,
    Training,
    TrainingAttendance,
    UserProfile,
)


class UzbekTokenObtainPairSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "Login yoki parol noto'g'ri.",
    }

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    club_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu login band. Boshqa login kiriting.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Parollar bir xil emas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        club_name = validated_data.pop("club_name", "") or PROJECT_CLUB_NAME
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        CoachProfile.objects.create(user=user, full_name=full_name, club_name=club_name)
        UserProfile.objects.get_or_create(user=user)
        return user


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    club_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()
    theme = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "full_name",
            "club_name",
            "role",
            "phone",
            "language",
            "theme",
        )
        read_only_fields = ("id", "username", "full_name")

    def _profile(self, obj):
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return profile

    def _coach_profile(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip() or obj.username
        coach_profile, _ = CoachProfile.objects.get_or_create(user=obj, defaults={"full_name": full_name})
        return coach_profile

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def get_club_name(self, obj):
        return self._coach_profile(obj).club_name

    def get_role(self, obj):
        return self._coach_profile(obj).role

    def get_phone(self, obj):
        return self._profile(obj).phone or self._coach_profile(obj).phone

    def get_language(self, obj):
        return self._profile(obj).language

    def get_theme(self, obj):
        return self._profile(obj).theme


class SettingsSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    club_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    role = serializers.CharField(max_length=100, required=False, allow_blank=True)
    language = serializers.ChoiceField(choices=UserProfile.LANGUAGE_CHOICES, required=False)
    theme = serializers.ChoiceField(choices=UserProfile.THEME_CHOICES, required=False)
    email_notifications = serializers.BooleanField(required=False)
    sms_notifications = serializers.BooleanField(required=False)
    system_alerts = serializers.BooleanField(required=False)

    def update(self, instance, validated_data):
        user = instance
        profile, _ = UserProfile.objects.get_or_create(user=user)
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        coach_profile, _ = CoachProfile.objects.get_or_create(user=user, defaults={"full_name": full_name})

        for field in ("first_name", "last_name", "email"):
            if field in validated_data:
                setattr(user, field, validated_data[field])
        user.save()

        for field in ("phone", "language", "theme", "email_notifications", "sms_notifications", "system_alerts"):
            if field in validated_data:
                setattr(profile, field, validated_data[field])
        profile.save()

        for field in ("club_name", "role"):
            if field in validated_data:
                setattr(coach_profile, field, validated_data[field])
        if "phone" in validated_data:
            coach_profile.phone = validated_data["phone"]
        coach_profile.full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        coach_profile.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Amaldagi parol noto'g'ri.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class PlayerStatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerStatistic
        fields = ("matches_played", "goals", "assists", "rating")


class PlayerSerializer(serializers.ModelSerializer):
    position_display = serializers.CharField(source="get_position_display", read_only=True)
    photo_url = serializers.SerializerMethodField()
    attendance_percent = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    training_count = serializers.SerializerMethodField()
    absent_count = serializers.SerializerMethodField()
    late_count = serializers.SerializerMethodField()
    last_training_status = serializers.SerializerMethodField()
    game_statistics = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = (
            "id",
            "full_name",
            "shirt_number",
            "position",
            "position_display",
            "age",
            "nationality",
            "height",
            "weight",
            "join_date",
            "photo",
            "photo_url",
            "short_note",
            "attendance_percent",
            "average_rating",
            "training_count",
            "absent_count",
            "late_count",
            "last_training_status",
            "game_statistics",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")
        extra_kwargs = {"photo": {"required": False, "allow_null": True}}

    def get_photo_url(self, obj):
        if not obj.photo:
            return obj.avatar_url
        request = self.context.get("request")
        url = obj.photo_display_url
        return request.build_absolute_uri(url) if request else url

    def _attendance_stats(self, obj):
        if not hasattr(obj, "_api_attendance_stats"):
            obj._api_attendance_stats = calculate_player_attendance_stats(obj)
        return obj._api_attendance_stats

    def get_attendance_percent(self, obj):
        return self._attendance_stats(obj)["attendance_percent"]

    def get_average_rating(self, obj):
        return self._attendance_stats(obj)["average_rating"]

    def get_training_count(self, obj):
        return self._attendance_stats(obj)["total_marked_trainings"]

    def get_absent_count(self, obj):
        return self._attendance_stats(obj)["absent_trainings"]

    def get_late_count(self, obj):
        return self._attendance_stats(obj)["late_trainings"]

    def get_last_training_status(self, obj):
        record = (
            obj.training_attendance_records.select_related("training")
            .order_by("-training__training_date", "-training__start_time")
            .first()
        )
        if not record:
            return "Kiritilmagan"
        return record.get_attendance_status_display()

    def get_game_statistics(self, obj):
        stat = obj.statistics.first()
        if not stat:
            return {"matches_played": 0, "goals": 0, "assists": 0, "rating": 0}
        return PlayerStatisticSerializer(stat).data


class TrainingSerializer(serializers.ModelSerializer):
    training_type_display = serializers.CharField(source="get_training_type_display", read_only=True)
    duration_display = serializers.CharField(read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    attendance_percent = serializers.IntegerField(read_only=True)
    attendance_display = serializers.CharField(read_only=True)
    average_rating = serializers.SerializerMethodField()
    marked_count = serializers.SerializerMethodField()

    class Meta:
        model = Training
        fields = (
            "id",
            "title",
            "training_type",
            "training_type_display",
            "training_date",
            "start_time",
            "end_time",
            "duration_minutes",
            "duration_display",
            "location",
            "note",
            "attendance_total",
            "attendance_present",
            "attendance_percent",
            "attendance_display",
            "average_rating",
            "marked_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("attendance_total", "attendance_present", "created_at", "updated_at")

    def get_duration_minutes(self, obj):
        return get_training_duration_minutes(obj)

    def get_average_rating(self, obj):
        records = [record for record in obj.attendance_records.all() if record.attendance_status in ACTIVE_STATUSES]
        if not records:
            return 0
        return round(sum(item.rating for item in records) / len(records), 2)

    def get_marked_count(self, obj):
        return obj.attendance_records.count()


class TrainingAttendanceSerializer(serializers.ModelSerializer):
    player_detail = PlayerSerializer(source="player", read_only=True)
    training_detail = TrainingSerializer(source="training", read_only=True)
    attendance_status_display = serializers.SerializerMethodField()
    physical_condition_display = serializers.CharField(source="get_physical_condition_display", read_only=True)
    activity_level_display = serializers.CharField(source="get_activity_level_display", read_only=True)
    discipline_display = serializers.CharField(source="get_discipline_display", read_only=True)
    injury_status_display = serializers.CharField(source="get_injury_status_display", read_only=True)
    participation_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = TrainingAttendance
        fields = (
            "id",
            "training",
            "training_detail",
            "player",
            "player_detail",
            "attendance_status",
            "attendance_status_display",
            "physical_condition",
            "physical_condition_display",
            "activity_level",
            "activity_level_display",
            "discipline",
            "discipline_display",
            "rating",
            "attended_minutes",
            "training_duration_minutes",
            "participation_percent",
            "fatigue_level",
            "pain_level",
            "sleep_quality",
            "activity_score",
            "heart_rate",
            "blood_pressure",
            "body_temperature",
            "measured_weight",
            "measured_height",
            "oxygen_saturation",
            "respiratory_rate",
            "injury_status",
            "injury_status_display",
            "injury_note",
            "coach_note",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_attendance_status_display(self, obj):
        return obj.get_attendance_status_display()


class TrainingAttendanceBulkItemSerializer(serializers.Serializer):
    player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())
    attendance_status = serializers.ChoiceField(choices=TrainingAttendance.STATUS_CHOICES)
    physical_condition = serializers.ChoiceField(choices=TrainingAttendance.PHYSICAL_CHOICES)
    activity_level = serializers.ChoiceField(choices=TrainingAttendance.ACTIVITY_CHOICES)
    discipline = serializers.ChoiceField(choices=TrainingAttendance.DISCIPLINE_CHOICES)
    rating = serializers.IntegerField(min_value=1, max_value=10)
    fatigue_level = serializers.IntegerField(required=False, min_value=1, max_value=10)
    activity_score = serializers.IntegerField(required=False, min_value=1, max_value=10)
    pain_level = serializers.IntegerField(required=False, min_value=1, max_value=10)
    sleep_quality = serializers.IntegerField(required=False, min_value=1, max_value=10)
    heart_rate = serializers.IntegerField(required=False, allow_null=True, min_value=30, max_value=240)
    blood_pressure = serializers.CharField(required=False, allow_blank=True, max_length=20)
    body_temperature = serializers.DecimalField(required=False, allow_null=True, max_digits=4, decimal_places=1)
    measured_weight = serializers.DecimalField(required=False, allow_null=True, max_digits=5, decimal_places=1)
    measured_height = serializers.IntegerField(required=False, allow_null=True, min_value=80, max_value=230)
    oxygen_saturation = serializers.IntegerField(required=False, allow_null=True, min_value=50, max_value=100)
    respiratory_rate = serializers.IntegerField(required=False, allow_null=True, min_value=5, max_value=80)
    injury_status = serializers.ChoiceField(choices=TrainingAttendance.INJURY_CHOICES)
    injury_note = serializers.CharField(required=False, allow_blank=True, max_length=180)
    coach_note = serializers.CharField(required=False, allow_blank=True)
    attended_minutes = serializers.IntegerField(required=False, min_value=0)


class MatchSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    result_label = serializers.CharField(read_only=True)

    class Meta:
        model = Match
        fields = (
            "id",
            "home_team",
            "away_team",
            "home_logo_url",
            "away_logo_url",
            "match_date",
            "match_time",
            "stadium",
            "status",
            "status_display",
            "home_score",
            "away_score",
            "attendance",
            "referee",
            "possession_percent",
            "shots",
            "shots_on_target",
            "corners",
            "yellow_cards",
            "red_cards",
            "note",
            "result_label",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "result_label")


class ReportRequestSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(
        choices=("attendance", "performance", "matches", "player", "training", "month"),
        default="attendance",
        required=False,
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    player_id = serializers.IntegerField(required=False)
    training_id = serializers.IntegerField(required=False)
    month = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and start > end:
            raise serializers.ValidationError("Boshlanish sanasi tugash sanasidan keyin bo'lishi mumkin emas.")
        return attrs


class AIMessageSerializer(serializers.ModelSerializer):
    """AI xabar serializer"""
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = AIMessage
        fields = ("id", "role", "role_display", "content", "created_at")
        read_only_fields = ("id", "created_at")


class AIConversationSerializer(serializers.ModelSerializer):
    """AI suhbat serializer"""
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = AIConversation
        fields = ("id", "title", "is_active", "message_count", "last_message", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by("-created_at").first()
        if last_msg:
            preview = last_msg.content[:100] + "..." if len(last_msg.content) > 100 else last_msg.content
            return {
                "content": preview,
                "role": last_msg.role,
                "created_at": last_msg.created_at,
            }
        return None


class AIConversationDetailSerializer(serializers.ModelSerializer):
    """AI suhbat batafsil serializer (xabarlar bilan)"""
    messages = AIMessageSerializer(many=True, read_only=True)

    class Meta:
        model = AIConversation
        fields = ("id", "title", "is_active", "messages", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class AIChatRequestSerializer(serializers.Serializer):
    """AI chat so'rov serializer"""
    message = serializers.CharField(required=True, min_length=1, max_length=5000)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
