from collections import defaultdict
from datetime import date, datetime

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
from .models import Match, Player, PlayerStatistic, Training, TrainingAttendance


def success(data=None, message="Amal muvaffaqiyatli bajarildi.", status_code=status.HTTP_200_OK):
    return Response({"success": True, "message": message, "data": data or {}}, status=status_code)


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

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        training_type = self.request.query_params.get("training_type", "").strip()
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
        queryset = super().get_queryset()
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
        return queryset.order_by("-match_date", "-match_time")


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
        team_stats = calculate_team_attendance_stats()
        today = date.today()
        recent_trainings = Training.objects.order_by("-training_date", "-start_time")[:5]
        recent_matches = Match.objects.order_by("-match_date", "-match_time")[:5]
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
                "message": f"{record.player.full_name} jarohat nazoratida.",
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
        data = {
            "total_players": Player.objects.count(),
            "today_trainings": Training.objects.filter(training_date=today).count(),
            "team_attendance_percent": team_stats["average_attendance_percent"],
            "team_average_rating": team_stats["average_rating"],
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
            "warnings": warnings,
        }
        return success(data, "Boshqaruv paneli ma'lumotlari yuklandi.")


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
        completed = Match.objects.exclude(home_score__isnull=True).exclude(away_score__isnull=True)
        completed_list = list(completed)
        wins = sum(1 for item in completed_list if (item.home_score or 0) > (item.away_score or 0))
        draws = sum(1 for item in completed_list if (item.home_score or 0) == (item.away_score or 0))
        losses = sum(1 for item in completed_list if (item.home_score or 0) < (item.away_score or 0))
        goals_for = sum(item.home_score or 0 for item in completed_list)
        goals_against = sum(item.away_score or 0 for item in completed_list)
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


class ReportsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ReportRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        report_type = serializer.validated_data["report_type"]
        if report_type == "player":
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
