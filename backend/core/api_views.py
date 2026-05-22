from collections import defaultdict
from datetime import date, datetime, timedelta

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .attendance import (
    ACTIVE_STATUSES,
    calculate_all_player_stats,
    calculate_player_attendance_stats,
    calculate_team_attendance_stats,
    get_training_duration_minutes,
)
from .api_serializers import (
    ChangePasswordSerializer,
    MatchSerializer,
    PlayerSerializer,
    RegisterSerializer,
    ReportRequestSerializer,
    SettingsSerializer,
    TrainingAttendanceBulkItemSerializer,
    TrainingAttendanceSerializer,
    TrainingSerializer,
    UserSerializer,
    UzbekTokenObtainPairSerializer,
)
from .models import Match, Player, PlayerStatistic, PROJECT_CLUB_NAME, Training, TrainingAttendance


def success(data=None, message="Amal muvaffaqiyatli bajarildi.", status_code=status.HTTP_200_OK):
    return Response({"success": True, "message": message, "data": data or {}}, status=status_code)


def project_club_matches(queryset):
    return queryset.filter(
        Q(home_team__iexact=PROJECT_CLUB_NAME) | Q(away_team__iexact=PROJECT_CLUB_NAME)
    )


def project_club_score_pair(match):
    if match.home_score is None or match.away_score is None:
        return None
    if match.away_team.casefold() == PROJECT_CLUB_NAME.casefold():
        return match.away_score, match.home_score
    if match.home_team.casefold() == PROJECT_CLUB_NAME.casefold():
        return match.home_score, match.away_score
    return None


def project_club_fixture_name(match):
    if match.away_team.casefold() == PROJECT_CLUB_NAME.casefold():
        return f"{match.away_team} vs {match.home_team}"
    return f"{match.home_team} vs {match.away_team}"


def project_club_record(matches):
    wins = draws = losses = goals_for = goals_against = 0
    for match in matches:
        if match.status != Match.STATUS_PLAYED:
            continue
        score_pair = project_club_score_pair(match)
        if score_pair is None:
            continue
        our_score, opponent_score = score_pair
        goals_for += our_score
        goals_against += opponent_score
        if our_score > opponent_score:
            wins += 1
        elif our_score < opponent_score:
            losses += 1
        else:
            draws += 1
    return {
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": goals_for,
        "goals_against": goals_against,
    }


def update_training_attendance_totals(training):
    records = TrainingAttendance.objects.filter(training=training)
    total = records.count()
    active = records.filter(attendance_status__in=ACTIVE_STATUSES).count()
    training.attendance_total = total
    training.attendance_present = active
    training.save(update_fields=["attendance_total", "attendance_present", "updated_at"])


def activity_score_from_level(level, rating):
    if level == TrainingAttendance.ACTIVITY_HIGH:
        return max(rating, 8)
    if level == TrainingAttendance.ACTIVITY_LOW:
        return min(rating, 5)
    return rating


def fatigue_from_condition(condition):
    return {
        TrainingAttendance.PHYSICAL_EXCELLENT: 1,
        TrainingAttendance.PHYSICAL_GOOD: 2,
        TrainingAttendance.PHYSICAL_AVERAGE: 3,
        TrainingAttendance.PHYSICAL_TIRED: 4,
        TrainingAttendance.PHYSICAL_INJURED: 5,
    }.get(condition, 3)


def default_attended_minutes(training, attendance_status):
    duration = get_training_duration_minutes(training)
    if attendance_status == TrainingAttendance.STATUS_ABSENT:
        return 0
    return duration


class UzbekTokenObtainPairView(TokenObtainPairView):
    serializer_class = UzbekTokenObtainPairSerializer
    permission_classes = [AllowAny]


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return success(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            },
            "Ro'yxatdan o'tish muvaffaqiyatli yakunlandi.",
            status.HTTP_201_CREATED,
        )


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success(UserSerializer(request.user).data, "Foydalanuvchi ma'lumotlari yuklandi.")


class SettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success(UserSerializer(request.user).data, "Sozlamalar yuklandi.")

    def patch(self, request):
        serializer = SettingsSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return success(UserSerializer(user).data, "Sozlamalar saqlandi.")


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        update_session_auth_hash(request, user)
        return success({}, "Parol muvaffaqiyatli yangilandi.")


class PlayerViewSet(viewsets.ModelViewSet):
    serializer_class = PlayerSerializer
    queryset = Player.objects.prefetch_related("statistics", "training_attendance_records")

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        position = self.request.query_params.get("position", "").strip()
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search)
                | Q(nationality__icontains=search)
                | Q(short_note__icontains=search)
            )
        if position:
            queryset = queryset.filter(position=position)
        return queryset.order_by("shirt_number", "full_name")

    @action(detail=True, methods=["get"], url_path="profile")
    def profile(self, request, pk=None):
        player = self.get_object()
        records = list(
            TrainingAttendance.objects.filter(player=player)
            .select_related("training", "player")
            .order_by("-training__training_date", "-training__start_time")
        )
        stats = calculate_player_attendance_stats(player, records)
        progress = [
            {
                "training_id": record.training_id,
                "date": record.training.training_date.isoformat(),
                "title": record.training.title,
                "rating": record.rating,
                "attendance": record.get_attendance_status_display(),
            }
            for record in reversed(records[:5])
        ]
        comments = [
            {
                "date": record.training.training_date.isoformat(),
                "training": record.training.title,
                "comment": record.coach_note,
            }
            for record in records
            if record.coach_note
        ][:8]
        player_stat = player.statistics.first()
        data = {
            "player": PlayerSerializer(player, context={"request": request}).data,
            "stats": stats,
            "training_history": TrainingAttendanceSerializer(
                records, many=True, context={"request": request}
            ).data,
            "progress": progress,
            "comments": comments,
            "game_statistics": {
                "matches_played": player_stat.matches_played if player_stat else 0,
                "goals": player_stat.goals if player_stat else 0,
                "assists": player_stat.assists if player_stat else 0,
                "rating": float(player_stat.rating) if player_stat else 0,
            },
        }
        return success(data, "Futbolchi profili yuklandi.")


class TrainingViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingSerializer
    queryset = Training.objects.prefetch_related("attendance_records")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success(response.data, "Mashg'ulotlar yuklandi.")

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return success(response.data, "Mashg'ulot yaratildi.", status.HTTP_201_CREATED)

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        training_type = (
            self.request.query_params.get("type", "").strip()
            or self.request.query_params.get("training_type", "").strip()
        )
        selected_date = self.request.query_params.get("date", "").strip()
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(location__icontains=search))
        if training_type:
            queryset = queryset.filter(training_type=training_type)
        if selected_date:
            queryset = queryset.filter(training_date=selected_date)
        return queryset.order_by("-training_date", "-start_time")

    @action(detail=True, methods=["get", "post"], url_path="attendance")
    def attendance(self, request, pk=None):
        training = self.get_object()
        if request.method == "GET":
            existing_records = {
                item.player_id: item
                for item in TrainingAttendance.objects.filter(training=training).select_related("player", "training")
            }
            duration = get_training_duration_minutes(training)
            rows = []
            for player in Player.objects.all():
                record = existing_records.get(player.id)
                if record:
                    rows.append(TrainingAttendanceSerializer(record, context={"request": request}).data)
                else:
                    rows.append(
                        {
                            "id": None,
                            "training": training.id,
                            "player": player.id,
                            "player_detail": PlayerSerializer(player, context={"request": request}).data,
                            "attendance_status": TrainingAttendance.STATUS_PRESENT,
                            "attendance_status_display": "Qatnashdi",
                            "physical_condition": TrainingAttendance.PHYSICAL_GOOD,
                            "physical_condition_display": "Yaxshi",
                            "activity_level": TrainingAttendance.ACTIVITY_MEDIUM,
                            "activity_level_display": "O'rtacha",
                            "discipline": TrainingAttendance.DISCIPLINE_GOOD,
                            "discipline_display": "Yaxshi",
                            "rating": 7,
                            "attended_minutes": duration,
                            "training_duration_minutes": duration,
                            "participation_percent": 100,
                            "fatigue_level": 2,
                            "pain_level": 1,
                            "sleep_quality": 7,
                            "activity_score": 7,
                            "heart_rate": None,
                            "blood_pressure": "",
                            "body_temperature": None,
                            "measured_weight": None,
                            "measured_height": None,
                            "oxygen_saturation": None,
                            "respiratory_rate": None,
                            "injury_status": TrainingAttendance.INJURY_NO,
                            "injury_status_display": "Yo'q",
                            "injury_note": "",
                            "coach_note": "",
                        }
                    )
            return success(
                {
                    "training": TrainingSerializer(training, context={"request": request}).data,
                    "records": rows,
                },
                "Mashg'ulot davomadi yuklandi.",
            )

        items = request.data.get("records", request.data)
        serializer = TrainingAttendanceBulkItemSerializer(data=items, many=True)
        serializer.is_valid(raise_exception=True)
        duration = get_training_duration_minutes(training)
        saved = []
        with transaction.atomic():
            for item in serializer.validated_data:
                attendance_status = item["attendance_status"]
                rating = int(item["rating"])
                attended_minutes = item.get("attended_minutes")
                if attended_minutes is None:
                    attended_minutes = default_attended_minutes(training, attendance_status)
                attended_minutes = min(attended_minutes, duration)
                is_active = attendance_status in ACTIVE_STATUSES
                defaults = {
                    "attendance_status": attendance_status,
                    "physical_condition": item["physical_condition"],
                    "activity_level": item["activity_level"],
                    "discipline": item["discipline"],
                    "rating": rating,
                    "attended_minutes": attended_minutes if is_active else 0,
                    "training_duration_minutes": duration,
                    "fatigue_level": item.get("fatigue_level", fatigue_from_condition(item["physical_condition"])) if is_active else 1,
                    "pain_level": item.get("pain_level", 1) if is_active else 1,
                    "sleep_quality": item.get("sleep_quality", 7) if is_active else 7,
                    "activity_score": item.get("activity_score", activity_score_from_level(item["activity_level"], rating)) if is_active else 1,
                    "heart_rate": item.get("heart_rate") if is_active else None,
                    "blood_pressure": item.get("blood_pressure", "") if is_active else "",
                    "body_temperature": item.get("body_temperature") if is_active else None,
                    "measured_weight": item.get("measured_weight") if is_active else None,
                    "measured_height": item.get("measured_height") if is_active else None,
                    "oxygen_saturation": item.get("oxygen_saturation") if is_active else None,
                    "respiratory_rate": item.get("respiratory_rate") if is_active else None,
                    "injury_status": item["injury_status"],
                    "injury_note": item.get("injury_note", ""),
                    "coach_note": item.get("coach_note", ""),
                }
                record, _ = TrainingAttendance.objects.update_or_create(
                    training=training,
                    player=item["player"],
                    defaults=defaults,
                )
                saved.append(record)
            update_training_attendance_totals(training)
        return success(
            TrainingAttendanceSerializer(saved, many=True, context={"request": request}).data,
            "Mashg'ulot holatlari saqlandi va statistika yangilandi.",
        )


class TrainingAttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingAttendanceSerializer
    queryset = TrainingAttendance.objects.select_related("training", "player")

    def get_queryset(self):
        queryset = super().get_queryset()
        training_id = self.request.query_params.get("training")
        player_id = self.request.query_params.get("player")
        if training_id:
            queryset = queryset.filter(training_id=training_id)
        if player_id:
            queryset = queryset.filter(player_id=player_id)
        return queryset

    def perform_create(self, serializer):
        record = serializer.save()
        update_training_attendance_totals(record.training)

    def perform_update(self, serializer):
        record = serializer.save()
        update_training_attendance_totals(record.training)

    def perform_destroy(self, instance):
        training = instance.training
        instance.delete()
        update_training_attendance_totals(training)


class MatchViewSet(viewsets.ModelViewSet):
    serializer_class = MatchSerializer
    queryset = Match.objects.all()

    def get_queryset(self):
        queryset = project_club_matches(super().get_queryset())
        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        selected_date = self.request.query_params.get("date", "").strip()
        if search:
            queryset = queryset.filter(
                Q(home_team__icontains=search)
                | Q(away_team__icontains=search)
                | Q(stadium__icontains=search)
            )
        if status_value:
            queryset = queryset.filter(status=status_value)
        if selected_date:
            queryset = queryset.filter(match_date=selected_date)
        ordering = self.request.query_params.get("ordering", "-match_date").strip()
        if ordering in {"match_date", "-match_date", "match_time", "-match_time"}:
            return queryset.order_by(ordering, "-match_time")
        return queryset.order_by("-match_date", "-match_time")

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        queryset = self.get_queryset()
        matches = list(queryset)
        record = project_club_record(matches)
        return success(
            {
                "total": len(matches),
                "wins": record["wins"],
                "draws": record["draws"],
                "losses": record["losses"],
            },
            "O'yinlar statistikasi yuklandi.",
        )


class ChoicesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success(
            {
                "positions": [{"value": key, "label": value} for key, value in Player.POSITION_CHOICES],
                "training_types": [{"value": key, "label": value} for key, value in Training.TYPE_CHOICES],
                "match_statuses": [{"value": key, "label": value} for key, value in Match.STATUS_CHOICES],
                "attendance_statuses": [
                    {"value": key, "label": value}
                    for key, value in TrainingAttendance.STATUS_CHOICES
                ],
                "physical_conditions": [
                    {"value": key, "label": value} for key, value in TrainingAttendance.PHYSICAL_CHOICES
                ],
                "activity_levels": [
                    {"value": key, "label": value} for key, value in TrainingAttendance.ACTIVITY_CHOICES
                ],
                "disciplines": [
                    {"value": key, "label": value} for key, value in TrainingAttendance.DISCIPLINE_CHOICES
                ],
                "injury_statuses": [
                    {"value": key, "label": value} for key, value in TrainingAttendance.INJURY_CHOICES
                ],
            },
            "Tanlovlar yuklandi.",
        )


class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get("period", "month")
        if period not in {"week", "month", "season"}:
            period = "month"

        team_stats = calculate_team_attendance_stats()
        today = date.today()
        if period == "week":
            start_date = today - timedelta(days=today.weekday())
            previous_start = start_date - timedelta(days=7)
        elif period == "season":
            start_date = date(today.year if today.month >= 8 else today.year - 1, 8, 1)
            previous_start = date(start_date.year - 1, 8, 1)
        else:
            start_date = today.replace(day=1)
            previous_start = (start_date - timedelta(days=1)).replace(day=1)
        previous_end = start_date - timedelta(days=1)

        period_trainings = Training.objects.filter(training_date__gte=start_date, training_date__lte=today)
        previous_trainings = Training.objects.filter(training_date__gte=previous_start, training_date__lte=previous_end)
        period_records = list(
            TrainingAttendance.objects.filter(training__training_date__gte=start_date, training__training_date__lte=today)
            .select_related("player", "training")
        )
        previous_records = list(
            TrainingAttendance.objects.filter(training__training_date__gte=previous_start, training__training_date__lte=previous_end)
            .select_related("player", "training")
        )
        period_matches = list(project_club_matches(Match.objects.filter(match_date__gte=start_date, match_date__lte=today)))
        previous_matches = list(project_club_matches(Match.objects.filter(match_date__gte=previous_start, match_date__lte=previous_end)))

        def attendance_percent(records):
            if not records:
                return 0
            active = sum(1 for record in records if record.attendance_status in ACTIVE_STATUSES)
            return round((active / len(records)) * 100, 2)

        def average_rating(records):
            active = [record.rating for record in records if record.attendance_status in ACTIVE_STATUSES]
            return round(sum(active) / len(active), 2) if active else 0

        def pct_change(current, previous):
            if not previous:
                return 0 if not current else 100
            return round(((current - previous) / previous) * 100, 1)

        def diff(current, previous):
            return round(current - previous, 1)

        period_attendance = attendance_percent(period_records)
        previous_attendance = attendance_percent(previous_records)
        period_rating = average_rating(period_records)
        previous_rating = average_rating(previous_records)
        period_record = project_club_record(period_matches)
        previous_record = project_club_record(previous_matches)
        period_goals = period_record["goals_for"]
        previous_goals = previous_record["goals_for"]

        latest_trainings = list(Training.objects.order_by("-training_date", "-start_time")[:5])
        latest_training_ids = [training.id for training in latest_trainings]
        recent_activity = {}
        recent_records = (
            TrainingAttendance.objects.filter(training_id__in=latest_training_ids, attendance_status__in=ACTIVE_STATUSES)
            .select_related("player")
        )
        for record in recent_records:
            bucket = recent_activity.setdefault(record.player_id, {"player": record.player, "scores": []})
            bucket["scores"].append(record.activity_score or record.rating or 0)
        top_recent = None
        if recent_activity:
            top_recent = max(
                recent_activity.values(),
                key=lambda item: sum(item["scores"]) / len(item["scores"]) if item["scores"] else 0,
            )
            top_recent = {
                "player_id": top_recent["player"].id,
                "player_name": top_recent["player"].full_name,
                "average_activity": round(sum(top_recent["scores"]) / len(top_recent["scores"]), 2),
                "trainings_count": len(top_recent["scores"]),
            }

        recent_trainings = Training.objects.order_by("-training_date", "-start_time")[:5]
        recent_matches = project_club_matches(Match.objects.all()).order_by("-match_date", "-match_time")[:5]
        injured_records = (
            TrainingAttendance.objects.filter(
                Q(injury_status__in=[TrainingAttendance.INJURY_YES, TrainingAttendance.INJURY_RECOVERING])
                | Q(physical_condition=TrainingAttendance.PHYSICAL_INJURED)
            )
            .select_related("player", "training")
            .order_by("-training__training_date")[:8]
        )
        absent_today = TrainingAttendance.objects.filter(
            training__training_date=today,
            attendance_status=TrainingAttendance.STATUS_ABSENT,
        ).select_related("player", "training")[:8]
        warnings = [
            {
                "type": "Jarohat",
                "message": f"{record.player.full_name} jarohatda.",
                "date": record.training.training_date.isoformat(),
            }
            for record in injured_records[:4]
        ] + [
            {
                "type": "Davomad",
                "message": f"{record.player.full_name} bugungi mashg'ulotga kelmadi.",
                "date": record.training.training_date.isoformat(),
            }
            for record in absent_today[:4]
        ]
        latest_records_by_player = {}
        for record in TrainingAttendance.objects.select_related("player", "training").order_by(
            "player_id", "-training__training_date", "-training__start_time"
        ):
            latest_records_by_player.setdefault(record.player_id, []).append(record)
        consecutive_absent = []
        discipline_problems = []
        for records in latest_records_by_player.values():
            absents = 0
            for record in records[:3]:
                if record.attendance_status == TrainingAttendance.STATUS_ABSENT:
                    absents += 1
                else:
                    break
            if absents >= 3:
                consecutive_absent.append(
                    {
                        "type": "Ketma-ket kelmadi",
                        "message": f"{records[0].player.full_name} ketma-ket {absents} mashg'ulotga kelmadi.",
                        "date": records[0].training.training_date.isoformat(),
                    }
                )
            if sum(1 for record in records[:2] if record.discipline == TrainingAttendance.DISCIPLINE_PROBLEM) >= 2:
                discipline_problems.append(
                    {
                        "type": "Intizom",
                        "message": f"{records[0].player.full_name} intizom muammosi: so'nggi 2 mashg'ulot.",
                        "date": records[0].training.training_date.isoformat(),
                    }
                )
        today_unmarked = Training.objects.filter(training_date=today, attendance_total=0).order_by("start_time").first()
        smart_warnings = (consecutive_absent[:1] + discipline_problems[:1])
        if today_unmarked:
            smart_warnings.append(
                {
                    "type": "Bugungi mashg'ulot",
                    "message": f"Bugun {today_unmarked.title} ({today_unmarked.start_time.strftime('%H:%M')}, {today_unmarked.location}) - davomad belgilanmagan.",
                    "date": today.isoformat(),
                }
            )
        if not smart_warnings:
            smart_warnings = warnings[:3]

        latest_comments = [
            {
                "player_id": record.player_id,
                "player_name": record.player.full_name,
                "training": record.training.title,
                "comment": record.coach_note,
                "date": record.training.training_date.isoformat(),
            }
            for record in TrainingAttendance.objects.filter(coach_note__gt="")
            .select_related("player", "training")
            .order_by("-training__training_date", "-updated_at")[:5]
        ]

        match_wins = period_record["wins"]
        match_draws = period_record["draws"]
        match_losses = period_record["losses"]

        data = {
            "period": period,
            "period_label": {"week": "Bu hafta", "month": "Bu oy", "season": "Bu mavsum"}[period],
            "total_players": Player.objects.count(),
            "today_trainings": Training.objects.filter(training_date=today).count(),
            "team_attendance_percent": team_stats["average_attendance_percent"],
            "team_average_rating": team_stats["average_rating"],
            "period_stats": {
                "trainings_count": period_trainings.count(),
                "matches_count": len(period_matches),
                "match_record": {"wins": match_wins, "draws": match_draws, "losses": match_losses},
                "goals": period_goals,
                "average_attendance_percent": period_attendance,
                "average_rating": period_rating,
                "injury_related_count": sum(
                    1
                    for record in period_records
                    if record.injury_status in {TrainingAttendance.INJURY_YES, TrainingAttendance.INJURY_RECOVERING}
                    or record.physical_condition == TrainingAttendance.PHYSICAL_INJURED
                ),
                "trends": {
                    "trainings": pct_change(period_trainings.count(), previous_trainings.count()),
                    "matches": pct_change(len(period_matches), len(previous_matches)),
                    "goals": pct_change(period_goals, previous_goals),
                    "attendance": diff(period_attendance, previous_attendance),
                    "rating": diff(period_rating, previous_rating),
                },
            },
            "top_recent_active_player": top_recent,
            "recent_trainings": TrainingSerializer(recent_trainings, many=True, context={"request": request}).data,
            "recent_matches": MatchSerializer(recent_matches, many=True, context={"request": request}).data,
            "injured_players": [
                {
                    "player_id": record.player_id,
                    "player_name": record.player.full_name,
                    "training": record.training.title,
                    "injury_status": record.get_injury_status_display(),
                    "note": record.injury_note,
                }
                for record in injured_records
            ],
            "warnings": smart_warnings,
            "latest_comments": latest_comments,
        }
        return success(data, "Boshqaruv paneli ma'lumotlari yuklandi.")


def get_statistics_period(period):
    today = date.today()
    normalized = period if period in {"week", "month", "season"} else "month"
    if normalized == "week":
        start = today - timedelta(days=7)
    elif normalized == "season":
        start = date(today.year, 1, 1)
    else:
        start = today.replace(day=1)
    span = max((today - start).days + 1, 1)
    previous_end = start - timedelta(days=1)
    previous_start = start - timedelta(days=span)
    return normalized, start, today, previous_start, previous_end


def get_period_records(start, end):
    return list(
        TrainingAttendance.objects.filter(
            training__training_date__gte=start,
            training__training_date__lte=end,
        )
        .select_related("training", "player")
        .order_by("player__full_name", "-training__training_date", "-training__start_time")
    )


def period_record_metrics(records):
    active = [record for record in records if record.attendance_status in ACTIVE_STATUSES]
    return {
        "attendance_percent": round((len(active) / len(records)) * 100, 2) if records else 0,
        "average_rating": round(sum(record.rating for record in active) / len(active), 2) if active else 0,
        "average_activity": round(sum(record.activity_score for record in active) / len(active), 2) if active else 0,
    }


def latest_injury_count(records):
    latest = {}
    for record in sorted(records, key=lambda item: (item.training.training_date, item.training.start_time), reverse=True):
        latest.setdefault(record.player_id, record)
    return sum(
        1
        for record in latest.values()
        if record.injury_status in {TrainingAttendance.INJURY_YES, TrainingAttendance.INJURY_RECOVERING}
        or record.physical_condition == TrainingAttendance.PHYSICAL_INJURED
    )


def short_player_name(full_name):
    parts = [part for part in full_name.split() if part]
    if len(parts) < 2:
        return full_name
    return f"{parts[0][0]}. {' '.join(parts[1:])}"


def player_initials(full_name):
    return "".join(part[0] for part in full_name.split()[:2] if part).upper() or "PL"


def build_statistics_player_rows(start, end):
    records_by_player = defaultdict(list)
    for record in get_period_records(start, end):
        records_by_player[record.player_id].append(record)

    rows = []
    for player in Player.objects.prefetch_related("statistics").all():
        records = records_by_player.get(player.id, [])
        active = [record for record in records if record.attendance_status in ACTIVE_STATUSES]
        total = len(records)
        present = len(active)
        stat = player.statistics.first()
        rows.append(
            {
                "player_id": player.id,
                "full_name": player.full_name,
                "short_name": short_player_name(player.full_name),
                "initials": player_initials(player.full_name),
                "position": player.position,
                "position_display": player.get_position_display(),
                "present": present,
                "total": total,
                "avg_rating": round(sum(record.rating for record in active) / present, 2) if present else 0,
                "avg_activity": round(sum(record.activity_score for record in active) / present, 2) if present else 0,
                "goals": stat.goals if stat else 0,
                "assists": stat.assists if stat else 0,
                "attendance_percent": round((present / total) * 100, 2) if total else 0,
            }
        )
    return rows


class StatisticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _training_type_analysis():
        analysis = []
        for key, label in Training.TYPE_CHOICES:
            trainings = Training.objects.filter(training_type=key)
            records = TrainingAttendance.objects.filter(training__training_type=key)
            active = records.filter(attendance_status__in=ACTIVE_STATUSES).count()
            total = records.count()
            avg_rating = round(sum(item.rating for item in records) / total, 2) if total else 0
            analysis.append(
                {
                    "type": key,
                    "label": label,
                    "trainings_count": trainings.count(),
                    "attendance_percent": round((active / total) * 100, 2) if total else 0,
                    "average_rating": avg_rating,
                }
            )
        return analysis

    @staticmethod
    def _match_stats():
        completed = project_club_matches(Match.objects.exclude(home_score__isnull=True).exclude(away_score__isnull=True))
        completed_list = list(completed)
        record = project_club_record(completed_list)
        wins = record["wins"]
        draws = record["draws"]
        losses = record["losses"]
        goals_for = record["goals_for"]
        goals_against = record["goals_against"]
        total = len(completed_list)
        return {
            "total": total,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "win_percent": round((wins / total) * 100, 2) if total else 0,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_difference": goals_for - goals_against,
        }

    def get(self, request):
        period, start, end, previous_start, previous_end = get_statistics_period(request.query_params.get("period", "month"))
        current_records = get_period_records(start, end)
        previous_records = get_period_records(previous_start, previous_end)
        current_metrics = period_record_metrics(current_records)
        previous_metrics = period_record_metrics(previous_records)
        player_stats = calculate_all_player_stats()
        top_active = sorted(player_stats, key=lambda item: item["overall_activity_rating"], reverse=True)[:5]
        most_absent = sorted(player_stats, key=lambda item: item["absent_trainings"], reverse=True)[:5]
        injured_records = (
            TrainingAttendance.objects.filter(
                Q(injury_status__in=[TrainingAttendance.INJURY_YES, TrainingAttendance.INJURY_RECOVERING])
                | Q(physical_condition=TrainingAttendance.PHYSICAL_INJURED)
            )
            .select_related("player", "training")
            .order_by("-training__training_date")[:20]
        )
        team_stats = calculate_team_attendance_stats()
        data = {
            "period": period,
            "summary": {
                "attendance_percent": current_metrics["attendance_percent"],
                "average_rating": current_metrics["average_rating"],
                "average_activity": current_metrics["average_activity"],
                "injury_count": latest_injury_count(current_records),
                "trainings_count": Training.objects.filter(training_date__gte=start, training_date__lte=end).count(),
                "trends": {
                    "attendance": round(current_metrics["attendance_percent"] - previous_metrics["attendance_percent"], 2),
                    "rating": round(current_metrics["average_rating"] - previous_metrics["average_rating"], 2),
                    "activity": round(current_metrics["average_activity"] - previous_metrics["average_activity"], 2),
                    "injury": latest_injury_count(current_records) - latest_injury_count(previous_records),
                },
            },
            "team": team_stats,
            "players": player_stats,
            "top_active_players": top_active,
            "most_absent_players": most_absent,
            "injured_players": [
                {
                    "player_id": record.player_id,
                    "player_name": record.player.full_name,
                    "training": record.training.title,
                    "date": record.training.training_date.isoformat(),
                    "injury_status": record.get_injury_status_display(),
                    "note": record.injury_note or record.coach_note,
                }
                for record in injured_records
            ],
            "matches": self._match_stats(),
            "training_types": self._training_type_analysis(),
        }
        return success(data, "Statistika yangilandi.")


class StatisticsAttendanceTrendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _, start, end, _, _ = get_statistics_period(request.query_params.get("period", "month"))
        trainings = (
            Training.objects.filter(training_date__gte=start, training_date__lte=end)
            .prefetch_related("attendance_records")
            .order_by("training_date", "start_time")
        )
        return success(
            [
                {
                    "date": training.training_date.isoformat(),
                    "present": sum(1 for record in training.attendance_records.all() if record.attendance_status in ACTIVE_STATUSES),
                    "total": training.attendance_records.count(),
                }
                for training in trainings
            ],
            "Davomad dinamikasi yuklandi.",
        )


class StatisticsGoalsAssistsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        get_statistics_period(request.query_params.get("period", "month"))
        stats = PlayerStatistic.objects.select_related("player").order_by("-goals", "-assists", "player__full_name")[:8]
        return success(
            [
                {
                    "player_id": stat.player_id,
                    "player_name": short_player_name(stat.player.full_name),
                    "goals": stat.goals,
                    "assists": stat.assists,
                }
                for stat in stats
            ],
            "Gol va assist statistikasi yuklandi.",
        )


class StatisticsRankingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _, start, end, _, _ = get_statistics_period(request.query_params.get("period", "month"))
        rows = build_statistics_player_rows(start, end)
        return success(
            {
                "most_present": sorted(rows, key=lambda row: (row["present"], row["attendance_percent"]), reverse=True)[:5],
                "top_rated": sorted(
                    [row for row in rows if row["present"] >= 3],
                    key=lambda row: row["avg_rating"],
                    reverse=True,
                )[:5],
            },
            "Reytinglar yuklandi.",
        )


class StatisticsPlayersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _, start, end, _, _ = get_statistics_period(request.query_params.get("period", "month"))
        rows = build_statistics_player_rows(start, end)
        return success(
            sorted(rows, key=lambda row: (row["attendance_percent"], row["avg_rating"]), reverse=True),
            "Futbolchilar statistikasi yuklandi.",
        )


def build_player_report(player):
    records = list(
        TrainingAttendance.objects.filter(player=player)
        .select_related("training", "player")
        .order_by("-training__training_date")
    )
    stats = calculate_player_attendance_stats(player, records)
    stat = player.statistics.first()
    return {
        "title": f"{player.full_name} bo'yicha hisobot",
        "subtitle": "Futbolchi mashg'ulot davomadi, baholari va murabbiy izohlari",
        "summary": [
            {"label": "Qatnashuv foizi", "value": f"{stats['attendance_percent']}%"},
            {"label": "O'rtacha baho", "value": stats["average_rating"]},
            {"label": "Kelmagan mashg'ulotlar", "value": stats["absent_trainings"]},
            {"label": "O'yinlar", "value": stat.matches_played if stat else 0},
        ],
        "rows": [
            {
                "Sana": record.training.training_date.isoformat(),
                "Mashg'ulot": record.training.title,
                "Davomad": record.get_attendance_status_display(),
                "Holat": record.get_physical_condition_display(),
                "Baho": record.rating,
                "Izoh": record.coach_note,
            }
            for record in records
        ],
    }


def build_training_report(training):
    records = list(
        TrainingAttendance.objects.filter(training=training)
        .select_related("player", "training")
        .order_by("player__shirt_number", "player__full_name")
    )
    active = sum(1 for item in records if item.attendance_status in ACTIVE_STATUSES)
    avg_rating = round(sum(item.rating for item in records) / len(records), 2) if records else 0
    return {
        "title": f"{training.title} bo'yicha hisobot",
        "subtitle": f"{training.training_date.isoformat()} | {training.location}",
        "summary": [
            {"label": "Futbolchilar", "value": len(records)},
            {"label": "Kelganlar", "value": active},
            {"label": "Qatnashuv", "value": f"{round((active / len(records)) * 100, 2) if records else 0}%"},
            {"label": "O'rtacha baho", "value": avg_rating},
        ],
        "rows": [
            {
                "Futbolchi": record.player.full_name,
                "Davomad": record.get_attendance_status_display(),
                "Jismoniy holat": record.get_physical_condition_display(),
                "Faollik": record.get_activity_level_display(),
                "Intizom": record.get_discipline_display(),
                "Baho": record.rating,
                "Izoh": record.coach_note,
            }
            for record in records
        ],
    }


def build_month_report(month_value):
    try:
        month_date = datetime.strptime(month_value, "%Y-%m").date()
    except (TypeError, ValueError):
        month_date = date.today().replace(day=1)
    trainings = Training.objects.filter(training_date__year=month_date.year, training_date__month=month_date.month)
    records = TrainingAttendance.objects.filter(training__in=trainings).select_related("training", "player")
    by_player = defaultdict(list)
    for record in records:
        by_player[record.player].append(record)
    rows = []
    for player, player_records in by_player.items():
        stats = calculate_player_attendance_stats(player, player_records)
        rows.append(
            {
                "Futbolchi": player.full_name,
                "Mashg'ulotlar": stats["total_marked_trainings"],
                "Qatnashuv": f"{stats['attendance_percent']}%",
                "O'rtacha baho": stats["average_rating"],
                "Kelmagan": stats["absent_trainings"],
            }
        )
    month_label = month_date.strftime("%Y-%m")
    return {
        "title": f"{month_label} oyi bo'yicha hisobot",
        "subtitle": "Oy kesimidagi jamoa davomadi va baholari",
        "summary": [
            {"label": "Mashg'ulotlar", "value": trainings.count()},
            {"label": "Yozuvlar", "value": records.count()},
            {"label": "Futbolchilar", "value": len(by_player)},
            {"label": "Jamoa qatnashuvi", "value": f"{calculate_team_attendance_stats()['average_attendance_percent']}%"},
        ],
        "rows": rows,
    }


def get_report_range(validated_data):
    end = validated_data.get("end_date") or date.today()
    start = validated_data.get("start_date") or end.replace(day=1)
    return start, end


def get_range_player_records(start, end):
    records_by_player = defaultdict(list)
    records = get_period_records(start, end)
    for record in records:
        records_by_player[record.player_id].append(record)
    return records, records_by_player


def get_report_injury_record(records):
    return next(
        (
            record
            for record in sorted(
                records,
                key=lambda item: (item.training.training_date, item.training.start_time),
                reverse=True,
            )
            if record.injury_status in {TrainingAttendance.INJURY_YES, TrainingAttendance.INJURY_RECOVERING}
            or record.physical_condition == TrainingAttendance.PHYSICAL_INJURED
        ),
        None,
    )


def attendance_report_status(row, injury_record):
    if injury_record:
        return "Jarohatli", "red"
    if row["attendance_percent"] >= 95 and row["avg_rating"] >= 8:
        return "A'lo", "green"
    if row["attendance_percent"] >= 80:
        return "Yaxshi", "green"
    if row["attendance_percent"] >= 60:
        return "O'rtacha", "yellow"
    return "Past", "red"


def report_date_subtitle(start, end):
    return f"{start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}"


def build_attendance_range_report(start, end):
    records, records_by_player = get_range_player_records(start, end)
    statistics_rows = build_statistics_player_rows(start, end)
    rows = []
    injuries = []
    for item in statistics_rows:
        player_records = records_by_player.get(item["player_id"], [])
        absent = sum(1 for record in player_records if record.attendance_status == TrainingAttendance.STATUS_ABSENT)
        injury_record = get_report_injury_record(player_records)
        status_label, status_tone = attendance_report_status(item, injury_record)
        if injury_record:
            injuries.append(
                {
                    "player_id": item["player_id"],
                    "player_name": item["short_name"],
                    "status": injury_record.get_injury_status_display()
                    if injury_record.injury_status != TrainingAttendance.INJURY_NO
                    else "Jarohatli",
                    "tone": "yellow"
                    if injury_record.injury_status == TrainingAttendance.INJURY_RECOVERING
                    else "red",
                }
            )
        rows.append(
            {
                **item,
                "absent": absent,
                "status_label": status_label,
                "status_tone": status_tone,
            }
        )

    marked_rows = [row for row in rows if row["total"]]
    average_attendance = round(
        sum(row["attendance_percent"] for row in marked_rows) / len(marked_rows), 2
    ) if marked_rows else 0
    most_absent = sorted(
        [row for row in rows if row["absent"]],
        key=lambda row: (row["absent"], row["attendance_percent"]),
        reverse=True,
    )[:4]
    training_count = Training.objects.filter(training_date__gte=start, training_date__lte=end).count()
    return {
        "report_type": "attendance",
        "title": "Davomad hisoboti",
        "subtitle": report_date_subtitle(start, end),
        "summary": [
            {"label": "Mashg'ulotlar", "value": training_count},
            {"label": "O'rtacha davomad", "value": f"{average_attendance}%"},
            {"label": "Ko'p qolgan", "value": len(most_absent)},
            {"label": "Jami futbolchilar", "value": Player.objects.count()},
        ],
        "rows": sorted(rows, key=lambda row: (row["attendance_percent"], row["avg_rating"]), reverse=True),
        "most_absent": [
            {
                "player_id": row["player_id"],
                "player_name": row["short_name"],
                "absent": row["absent"],
            }
            for row in most_absent
        ],
        "injury_overview": {
            "players": injuries[:4],
            "healthy_count": max(Player.objects.count() - len({item["player_id"] for item in injuries}), 0),
        },
    }


def build_performance_range_report(start, end):
    rows = []
    records, records_by_player = get_range_player_records(start, end)
    for item in build_statistics_player_rows(start, end):
        player_records = records_by_player.get(item["player_id"], [])
        active = [record for record in player_records if record.attendance_status in ACTIVE_STATUSES]
        discipline_issues = sum(
            1 for record in active if record.discipline in {TrainingAttendance.DISCIPLINE_WARNING, TrainingAttendance.DISCIPLINE_PROBLEM}
        )
        status = "Barqaror"
        tone = "green"
        if item["avg_rating"] >= 8:
            status = "Yuqori"
        elif item["avg_rating"] and item["avg_rating"] < 6:
            status = "Nazorat"
            tone = "red"
        elif discipline_issues:
            status = "Intizom"
            tone = "yellow"
        rows.append({**item, "discipline_issues": discipline_issues, "status_label": status, "status_tone": tone})

    active_rows = [row for row in rows if row["present"]]
    average_rating = round(sum(row["avg_rating"] for row in active_rows) / len(active_rows), 2) if active_rows else 0
    average_activity = round(sum(row["avg_activity"] for row in active_rows) / len(active_rows), 2) if active_rows else 0
    return {
        "report_type": "performance",
        "title": "Samaradorlik hisoboti",
        "subtitle": report_date_subtitle(start, end),
        "summary": [
            {"label": "Baholangan futbolchilar", "value": len(active_rows)},
            {"label": "O'rtacha baho", "value": average_rating},
            {"label": "O'rtacha faollik", "value": average_activity},
            {"label": "Intizom signali", "value": sum(1 for row in rows if row["discipline_issues"])},
        ],
        "rows": sorted(rows, key=lambda row: (row["avg_rating"], row["avg_activity"]), reverse=True),
        "top_rating": [
            {"player_id": row["player_id"], "player_name": row["short_name"], "value": row["avg_rating"]}
            for row in sorted(active_rows, key=lambda row: row["avg_rating"], reverse=True)[:4]
        ],
        "top_activity": [
            {"player_id": row["player_id"], "player_name": row["short_name"], "value": row["avg_activity"]}
            for row in sorted(active_rows, key=lambda row: row["avg_activity"], reverse=True)[:4]
        ],
    }


def build_matches_range_report(start, end):
    matches = list(
        project_club_matches(Match.objects.filter(match_date__gte=start, match_date__lte=end))
        .order_by("-match_date", "-match_time")
    )
    record = project_club_record(matches)
    return {
        "report_type": "matches",
        "title": "O'yinlar hisoboti",
        "subtitle": report_date_subtitle(start, end),
        "summary": [
            {"label": "Jami o'yin", "value": len(matches)},
            {"label": "G'alaba", "value": record["wins"]},
            {"label": "Durang", "value": record["draws"]},
            {"label": "Mag'lubiyat", "value": record["losses"]},
        ],
        "rows": [
            {
                "id": match.id,
                "date": match.match_date.isoformat(),
                "fixture": project_club_fixture_name(match),
                "stadium": match.stadium,
                "score": "-" if match.home_score is None or match.away_score is None else f"{match.home_score} - {match.away_score}",
                "result": match.result_label,
                "status": match.get_status_display(),
                "shots": match.shots,
                "shots_on_target": match.shots_on_target,
                "corners": match.corners,
            }
            for match in matches
        ],
    }


class ReportsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ReportRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        report_type = serializer.validated_data["report_type"]
        if report_type == "attendance":
            report = build_attendance_range_report(*get_report_range(serializer.validated_data))
        elif report_type == "performance":
            report = build_performance_range_report(*get_report_range(serializer.validated_data))
        elif report_type == "matches":
            report = build_matches_range_report(*get_report_range(serializer.validated_data))
        elif report_type == "player":
            player_id = serializer.validated_data.get("player_id")
            player = Player.objects.filter(id=player_id).first() or Player.objects.first()
            if not player:
                return success({"title": "Hisobot", "summary": [], "rows": []}, "Futbolchi topilmadi.")
            report = build_player_report(player)
        elif report_type == "training":
            training_id = serializer.validated_data.get("training_id")
            training = Training.objects.filter(id=training_id).first() or Training.objects.order_by("-training_date").first()
            if not training:
                return success({"title": "Hisobot", "summary": [], "rows": []}, "Mashg'ulot topilmadi.")
            report = build_training_report(training)
        else:
            report = build_month_report(serializer.validated_data.get("month"))
        return success(report, "Hisobot tayyorlandi.")


class ReportPrintAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        response = ReportsAPIView().get(request)
        report = response.data.get("data", {})
        rows = report.get("rows", [])
        headers = list(rows[0].keys()) if rows else []
        html = [
            "<!doctype html><html lang='uz'><head><meta charset='utf-8'>",
            "<title>Hisobot</title>",
            "<style>body{font-family:Arial,sans-serif;color:#111827;padding:32px}"
            "h1{margin:0 0 8px}table{width:100%;border-collapse:collapse;margin-top:24px}"
            "th,td{border:1px solid #d1d5db;padding:8px;text-align:left;font-size:13px}"
            ".summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:20px}"
            ".card{border:1px solid #d1d5db;padding:12px}.label{color:#64748b;font-size:12px}"
            "@media print{button{display:none}}</style></head><body>",
            "<button onclick='window.print()'>Chop etish</button>",
            f"<h1>{report.get('title', 'Hisobot')}</h1>",
            f"<p>{report.get('subtitle', '')}</p><div class='summary'>",
        ]
        for item in report.get("summary", []):
            html.append(f"<div class='card'><div class='label'>{item['label']}</div><strong>{item['value']}</strong></div>")
        html.append("</div><table><thead><tr>")
        for header in headers:
            html.append(f"<th>{header}</th>")
        html.append("</tr></thead><tbody>")
        for row in rows:
            html.append("<tr>")
            for header in headers:
                html.append(f"<td>{row.get(header, '')}</td>")
            html.append("</tr>")
        html.append("</tbody></table></body></html>")
        return HttpResponse("".join(html))
