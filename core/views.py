import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import activate
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .attendance import (
    build_default_record,
    calculate_all_player_stats,
    calculate_player_attendance_stats,
    calculate_team_attendance_stats,
    get_training_duration_minutes,
    serialize_attendance,
    serialize_player,
    serialize_training,
)
from .forms import LoginForm, MatchForm, PlayerForm, StyledPasswordChangeForm, TrainingForm, UserSettingsForm
from .models import Match, Player, PlayerStatistic, TeamStatistic, Training, TrainingAttendance, UserProfile


class UzbekLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "auth/login.html"
    redirect_authenticated_user = True


@method_decorator(login_required, name="dispatch")
class DashboardView(TemplateView):
    template_name = "dashboard/index.html"

    @staticmethod
    def _build_line_points(values, width=520, height=230, padding_x=18, padding_y=18):
        if not values:
            return ""
        max_value = max(values) or 1
        step_x = (width - padding_x * 2) / max(len(values) - 1, 1)
        points = []
        for index, value in enumerate(values):
            x_pos = padding_x + (step_x * index)
            y_pos = height - padding_y - ((value / max_value) * (height - padding_y * 2))
            points.append(f"{round(x_pos, 2)},{round(y_pos, 2)}")
        return " ".join(points)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attendance_summary = calculate_team_attendance_stats()
        top_attendance_player = attendance_summary["top_player"]["player_name"] if attendance_summary["top_player"] else "-"
        context["stats"] = [
            {
                "title": "Jami futbolchilar",
                "metric_value": str(Player.objects.count() or 37),
                "change_text": "Tarkib nazorati",
                "accent": "blue",
                "trend_value": "+4.8%",
                "trend_direction": "up",
            },
            {
                "title": "Mashgulotlar",
                "metric_value": str(Training.objects.count()),
                "change_text": "Haftalik reja",
                "accent": "green",
                "trend_value": "-1.4%",
                "trend_direction": "down",
            },
            {
                "title": "Gol va assist",
                "metric_value": str(sum(item.goals + item.assists for item in PlayerStatistic.objects.all())),
                "change_text": "Jamoa hissasi",
                "accent": "purple",
                "trend_value": "+6.9%",
                "trend_direction": "up",
            },
            {
                "title": "O'rtacha davomad",
                "metric_value": f"{attendance_summary['average_attendance_percent']}%",
                "change_text": "Mashg'ulot intizomi",
                "accent": "cyan",
                "trend_value": "Davomad",
                "trend_direction": "up",
            },
            {
                "title": "O'rtacha faollik",
                "metric_value": f"{attendance_summary['average_activity_score']}/10",
                "change_text": "Mashg'ulot bahosi",
                "accent": "green",
                "trend_value": "Faollik",
                "trend_direction": "up",
            },
            {
                "title": "Bugungi davomad",
                "metric_value": f"{attendance_summary['today_attendance_percent']}%",
                "change_text": "Bugungi mashg'ulot",
                "accent": "blue",
                "trend_value": "Bugun",
                "trend_direction": "up",
            },
            {
                "title": "Eng faol futbolchi",
                "metric_value": top_attendance_player,
                "change_text": "Umumiy reyting bo'yicha",
                "accent": "purple",
                "trend_value": "Top",
                "trend_direction": "up",
            },
            {
                "title": "Jarohat cheklovi",
                "metric_value": str(attendance_summary["injury_related_count"]),
                "change_text": "Bor yoki tiklanmoqda",
                "accent": "purple",
                "trend_value": "Nazorat",
                "trend_direction": "down" if attendance_summary["injury_related_count"] else "up",
            },
        ]
        players = list(Player.objects.prefetch_related("statistics").all())
        for player in players:
            player.dashboard_stat = next(iter(player.statistics.all()), None)
        context["players"] = sorted(
            players,
            key=lambda player: (
                player.dashboard_stat.rating if player.dashboard_stat else 0,
                player.dashboard_stat.goals if player.dashboard_stat else 0,
                player.dashboard_stat.matches_played if player.dashboard_stat else 0,
            ),
            reverse=True,
        )[:5]
        context["upcoming_trainings"] = Training.objects.all()[:4]
        charts = {
            "labels": ["Yan", "Fev", "Mar", "Apr", "May", "Iyun"],
            "wins": [3, 4, 5, 4, 6, 6],
            "effectiveness": [70, 74, 76, 73, 84, 91],
            "goals": [10, 11, 13, 12, 18, 16],
            "has_performance_data": True,
            "has_goals_data": True,
        }
        performance_best_index = charts["effectiveness"].index(max(charts["effectiveness"]))
        performance_low_index = charts["effectiveness"].index(min(charts["effectiveness"]))
        performance_average = round(sum(charts["effectiveness"]) / len(charts["effectiveness"]))
        performance_trend = charts["effectiveness"][-1] - charts["effectiveness"][-2]
        goals_best_index = charts["goals"].index(max(charts["goals"]))
        goals_low_index = charts["goals"].index(min(charts["goals"]))
        goals_total = sum(charts["goals"])
        goals_average = goals_total / len(charts["goals"])
        goals_trend = ((charts["goals"][-1] - charts["goals"][0]) / charts["goals"][0]) * 100
        goals_stability = round(100 - ((max(charts["goals"]) - min(charts["goals"])) / max(charts["goals"]) * 100))
        performance_stability = round(100 - ((max(charts["effectiveness"]) - min(charts["effectiveness"])) / 100 * 100))
        charts["effectiveness_points"] = self._build_line_points(charts["effectiveness"])
        charts["wins_points"] = self._build_line_points(charts["wins"])
        max_goals = max(charts["goals"]) if charts["goals"] else 1
        charts["goal_bars"] = [
            {"label": label, "value": value, "height": max(round((value / max_goals) * 100), 18)}
            for label, value in zip(charts["labels"], charts["goals"])
        ]
        charts["performance_summary"] = {
            "kpi": f"{performance_average}%",
            "trend": f"+{performance_trend}%",
            "trend_direction": "up" if performance_trend >= 0 else "down",
            "best_label": charts["labels"][performance_best_index],
            "best_value": f"{charts['effectiveness'][performance_best_index]}%",
            "low_label": charts["labels"][performance_low_index],
            "low_value": f"{charts['effectiveness'][performance_low_index]}%",
            "stability": f"{performance_stability}%",
        }
        charts["goals_summary"] = {
            "kpi": goals_total,
            "trend": f"+{round(goals_trend)}%",
            "trend_direction": "up" if goals_trend >= 0 else "down",
            "best_label": charts["labels"][goals_best_index],
            "best_value": charts["goals"][goals_best_index],
            "low_label": charts["labels"][goals_low_index],
            "low_value": charts["goals"][goals_low_index],
            "average": f"{goals_average:.1f}",
            "stability": f"{goals_stability}%",
        }
        context["charts"] = charts
        return context


@method_decorator(login_required, name="dispatch")
class PlayerListView(ListView):
    model = Player
    template_name = "players/list.html"
    context_object_name = "players"

    def get_queryset(self):
        queryset = Player.objects.prefetch_related(
            Prefetch("statistics", queryset=PlayerStatistic.objects.all())
        )
        search = self.request.GET.get("q", "").strip()
        position = self.request.GET.get("position", "").strip()
        if search:
            queryset = queryset.filter(full_name__icontains=search)
        if position:
            queryset = queryset.filter(position=position)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        context["selected_position"] = self.request.GET.get("position", "")
        context["position_choices"] = Player.POSITION_CHOICES
        return context


@method_decorator(login_required, name="dispatch")
class PlayerDetailView(DetailView):
    model = Player
    template_name = "players/detail.html"
    context_object_name = "player"

    @staticmethod
    def _percent(value, max_value):
        if not max_value:
            return 0
        return min(round((value / max_value) * 100), 100)

    @staticmethod
    def _format_decimal(value, digits=2):
        return f"{value:.{digits}f}".rstrip("0").rstrip(".")

    @staticmethod
    def _format_join_date(value):
        months = [
            "yanvar",
            "fevral",
            "mart",
            "aprel",
            "may",
            "iyun",
            "iyul",
            "avgust",
            "sentabr",
            "oktabr",
            "noyabr",
            "dekabr",
        ]
        return f"{value.day} {months[value.month - 1]} {value.year}"

    @staticmethod
    def _tenure_months(join_date):
        today = date.today()
        return max(
            (today.year - join_date.year) * 12
            + today.month
            - join_date.month
            - (1 if today.day < join_date.day else 0),
            0,
        )

    @classmethod
    def _format_tenure(cls, join_date):
        total_months = cls._tenure_months(join_date)
        years, months = divmod(total_months, 12)
        parts = []
        if years:
            parts.append(f"{years} yil")
        if months:
            parts.append(f"{months} oy")
        return " ".join(parts) or "1 oydan kam"

    def get_queryset(self):
        return Player.objects.prefetch_related(
            Prefetch("statistics", queryset=PlayerStatistic.objects.all())
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stat = self.object.statistics.first()
        all_stats = list(PlayerStatistic.objects.all())

        matches = stat.matches_played if stat else 0
        goals = stat.goals if stat else 0
        assists = stat.assists if stat else 0
        rating = float(stat.rating) if stat else 0
        goal_contributions = goals + assists
        contribution_per_match = goal_contributions / matches if matches else 0

        max_matches = max((item.matches_played for item in all_stats), default=0)
        max_contributions = max((item.goals + item.assists for item in all_stats), default=0)
        max_contribution_rate = max(
            (
                (item.goals + item.assists) / item.matches_played
                for item in all_stats
                if item.matches_played
            ),
            default=0,
        )

        matches_percent = self._percent(matches, max_matches)
        contribution_percent = self._percent(goal_contributions, max_contributions)
        rate_percent = self._percent(contribution_per_match, max_contribution_rate)
        rating_percent = min(round(rating * 10), 100)
        tenure = self._format_tenure(self.object.join_date)
        tenure_percent = min(round((self._tenure_months(self.object.join_date) / 60) * 100), 100)

        if self.object.position == Player.POSITION_GOALKEEPER:
            role_percent = round(matches_percent * 0.60 + rating_percent * 0.40)
            overall_score = round(matches_percent * 0.45 + rating_percent * 0.45 + tenure_percent * 0.10)
            performance_caption = "O'yin amaliyoti, reyting va klub tajribasi asosida"
            performance_metrics = [
                {
                    "label": "O'yin amaliyoti",
                    "percent": matches_percent,
                    "value": f"{matches} o'yin",
                    "caption": "Jamoa ichidagi eng yuqori ko'rsatkichga nisbatan",
                    "accent": "blue",
                },
                {
                    "label": "Murabbiy reytingi",
                    "percent": rating_percent,
                    "value": f"{rating:.1f} / 10",
                    "caption": "Umumiy baholash shkalasi",
                    "accent": "gold",
                },
                {
                    "label": "Tarkib ishonchi",
                    "percent": role_percent,
                    "value": f"{role_percent}%",
                    "caption": "O'yin amaliyoti va reyting kombinatsiyasi",
                    "accent": "purple",
                },
                {
                    "label": "Klub tajribasi",
                    "percent": tenure_percent,
                    "value": tenure,
                    "caption": "5 yillik barqarorlik mezoniga nisbatan",
                    "accent": "green",
                },
            ]
        else:
            performance_caption = "O'yin amaliyoti, gol hissasi va reyting asosida"
            if self.object.position == Player.POSITION_DEFENDER:
                overall_score = round(
                    matches_percent * 0.35
                    + contribution_percent * 0.15
                    + rate_percent * 0.10
                    + rating_percent * 0.40
                )
            elif self.object.position == Player.POSITION_MIDFIELDER:
                overall_score = round(
                    matches_percent * 0.20
                    + contribution_percent * 0.30
                    + rate_percent * 0.20
                    + rating_percent * 0.30
                )
            else:
                overall_score = round(
                    matches_percent * 0.20
                    + contribution_percent * 0.40
                    + rate_percent * 0.25
                    + rating_percent * 0.15
                )
            performance_metrics = [
                {
                    "label": "O'yin amaliyoti",
                    "percent": matches_percent,
                    "value": f"{matches} o'yin",
                    "caption": "Jamoa ichidagi eng yuqori ko'rsatkichga nisbatan",
                    "accent": "blue",
                },
                {
                    "label": "Gol yaratish",
                    "percent": contribution_percent,
                    "value": f"{goal_contributions} hissa",
                    "caption": "Gol va golli uzatmalar yig'indisi",
                    "accent": "green",
                },
                {
                    "label": "O'rtacha hissa",
                    "percent": rate_percent,
                    "value": f"{self._format_decimal(contribution_per_match)} / o'yin",
                    "caption": "Har bir o'yinga to'g'ri keladigan gol hissasi",
                    "accent": "purple",
                },
                {
                    "label": "Murabbiy reytingi",
                    "percent": rating_percent,
                    "value": f"{rating:.1f} / 10",
                    "caption": "Umumiy baholash shkalasi",
                    "accent": "gold",
                },
            ]

        if overall_score >= 85:
            performance_status = "Elita forma"
        elif overall_score >= 70:
            performance_status = "Barqaror forma"
        elif overall_score >= 50:
            performance_status = "O'sish zonasi"
        else:
            performance_status = "Qo'shimcha e'tibor"

        context["stat"] = stat
        context["career_summary"] = [
            {"label": "Jamoada", "value": tenure},
            {"label": "Gol hissasi", "value": f"{goal_contributions} ta"},
            {"label": "Har o'yinda", "value": self._format_decimal(contribution_per_match)},
        ]
        context["career_items"] = [
            {
                "icon": "bi-calendar2-check",
                "label": "Jamoaga qo'shildi",
                "value": self._format_join_date(self.object.join_date),
                "hint": f"{tenure} davomida tarkibda",
            },
            {
                "icon": "bi-diagram-3",
                "label": "Asosiy pozitsiya",
                "value": self.object.get_position_display(),
                "hint": "Taktik roli va maydondagi zonasi",
            },
            {
                "icon": "bi-hash",
                "label": "Forma raqami",
                "value": f"#{self.object.shirt_number}",
                "hint": "Tarkib identifikatori",
            },
            {
                "icon": "bi-journal-text",
                "label": "Murabbiy izohi",
                "value": self.object.short_note or "Izoh kiritilmagan",
                "hint": "Profil bo'yicha qisqa qayd",
            },
        ]
        context["performance_summary"] = {
            "score": overall_score,
            "status": performance_status,
            "caption": performance_caption,
        }
        context["performance_metrics"] = performance_metrics
        return context


@method_decorator(login_required, name="dispatch")
class PlayerCreateView(CreateView):
    model = Player
    form_class = PlayerForm
    template_name = "players/form.html"

    def form_valid(self, form):
        messages.success(self.request, "Futbolchi muvaffaqiyatli qo'shildi.")
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class PlayerUpdateView(UpdateView):
    model = Player
    form_class = PlayerForm
    template_name = "players/form.html"

    def form_valid(self, form):
        messages.success(self.request, "Futbolchi ma'lumotlari yangilandi.")
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class PlayerDeleteView(DeleteView):
    model = Player
    template_name = "players/confirm_delete.html"
    success_url = reverse_lazy("player_list")

    def form_valid(self, form):
        messages.success(self.request, "Futbolchi muvaffaqiyatli o'chirildi.")
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class MatchListView(ListView):
    model = Match
    template_name = "matches/list.html"
    context_object_name = "matches"

    def get_queryset(self):
        queryset = Match.objects.all()
        tab = self.request.GET.get("status", "all")
        selected_date = self.request.GET.get("date", "")
        if tab != "all":
            queryset = queryset.filter(status=tab)
        if selected_date:
            queryset = queryset.filter(match_date=selected_date)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_tab"] = self.request.GET.get("status", "all")
        context["selected_date"] = self.request.GET.get("date", "")
        context["tabs"] = [
            {"id": "all", "label": "Barchasi"},
            {"id": "upcoming", "label": "Kelgusi"},
            {"id": "live", "label": "Jonli"},
            {"id": "played", "label": "Tugagan"},
        ]
        context["counts"] = {
            "upcoming": Match.objects.filter(status=Match.STATUS_UPCOMING).count(),
            "live": Match.objects.filter(status=Match.STATUS_LIVE).count(),
            "played": Match.objects.filter(status=Match.STATUS_PLAYED).count(),
        }
        return context


@method_decorator(login_required, name="dispatch")
class MatchDetailView(DetailView):
    model = Match
    template_name = "matches/detail.html"
    context_object_name = "match"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        home = self.object.home_score or 0
        away = self.object.away_score or 0
        match_status = self.object.status
        if match_status != Match.STATUS_UPCOMING:
            if home > away:
                context["winner"] = "home"
            elif away > home:
                context["winner"] = "away"
            else:
                context["winner"] = "draw"
        else:
            context["winner"] = "none"

        stat_rows = [
            ("Topga egalik", 58, 42, "%"),
            ("Zarbalar", max(home * 4, 6), max(away * 4, 4), ""),
            ("Aniq zarbalar", max(home * 2, 3), max(away * 2, 2), ""),
            ("Kornerlar", max(home + 4, 4), max(away + 3, 3), ""),
            ("Qoidabuzarliklar", max(10 - home, 6), max(9 - away, 5), ""),
        ]
        enriched_stats = []
        for label, left, right, suffix in stat_rows:
            total = (left + right) or 1
            left_width = round((left / total) * 100, 1)
            right_width = round((right / total) * 100, 1)
            diff = abs(left - right)
            leader = "home" if left > right else "away" if right > left else "draw"
            enriched_stats.append(
                {
                    "label": label,
                    "left": left,
                    "right": right,
                    "suffix": suffix,
                    "left_width": left_width,
                    "right_width": right_width,
                    "diff": diff,
                    "leader": leader,
                    "advantage_text": "Teng" if diff == 0 else f"+{diff} ustunlik",
                }
            )
        context["stat_rows"] = enriched_stats

        context["match_info_cards"] = [
            {"icon": "bi-geo-alt", "label": "Stadion", "value": self.object.stadium},
            {"icon": "bi-people", "label": "Tomoshabinlar", "value": f"{self.object.attendance or 0:,}".replace(",", " ")},
            {"icon": "bi-award", "label": "Hakam", "value": self.object.referee or "Belgilanmagan"},
        ]
        context["match_events"] = self._build_match_events()
        return context

    def _build_match_events(self):
        home = self.object.home_team
        away = self.object.away_team
        if self.object.status == Match.STATUS_UPCOMING:
            return []

        base_events = [
            {"minute": "12'", "team": "home", "type": "goal", "title": f"{home} gol urdi", "player": "Asosiy hujumchi"},
            {"minute": "28'", "team": "away", "type": "card", "title": f"{away} sariq kartochka oldi", "player": "Markaziy himoyachi"},
            {"minute": "46'", "team": "home", "type": "sub", "title": f"{home} almashtirish qildi", "player": "Yarim himoyachi -> Hujumchi"},
            {"minute": "61'", "team": "away", "type": "goal", "title": f"{away} javob golini urdi", "player": "Qanot hujumchisi"},
            {"minute": "77'", "team": "home", "type": "goal", "title": f"{home} hal qiluvchi hujum", "player": "Pleymeyker"},
            {"minute": "84'", "team": "away", "type": "sub", "title": f"{away} tarkibni yangiladi", "player": "Himoyachi -> Yarim himoyachi"},
        ]
        if self.object.status == Match.STATUS_LIVE:
            return base_events[:4]
        return base_events


@method_decorator(login_required, name="dispatch")
class MatchCreateView(CreateView):
    model = Match
    form_class = MatchForm
    template_name = "matches/form.html"

    def form_valid(self, form):
        messages.success(self.request, "Oyin muvaffaqiyatli qo'shildi.")
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class MatchUpdateView(UpdateView):
    model = Match
    form_class = MatchForm
    template_name = "matches/form.html"

    def form_valid(self, form):
        messages.success(self.request, "Oyin ma'lumotlari yangilandi.")
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class TrainingListView(ListView):
    model = Training
    template_name = "training/list.html"
    context_object_name = "trainings"

    def get_queryset(self):
        queryset = Training.objects.all()
        selected_type = self.request.GET.get("type", "")
        selected_date = self.request.GET.get("date", "")
        if selected_type:
            queryset = queryset.filter(training_type=selected_type)
        if selected_date:
            queryset = queryset.filter(training_date=selected_date)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_type"] = self.request.GET.get("type", "")
        context["selected_date"] = self.request.GET.get("date", "")
        context["type_choices"] = Training.TYPE_CHOICES
        all_trainings = list(Training.objects.all())
        avg_attendance = (
            round(sum(item.attendance_percent for item in all_trainings) / len(all_trainings))
            if all_trainings
            else 0
        )
        context["completed_trainings"] = Training.objects.filter(
            training_date__lt=date.today()
        ).order_by("-training_date", "-start_time")[:6]
        context["training_stats"] = [
            ("Bugungi mashgulotlar", Training.objects.filter(training_date=date.today()).count(), "Rejalashtirilgan", "blue"),
            ("Haftalik mashgulotlar", len(all_trainings), "Umumiy reja", "cyan"),
            ("Ortacha qatnashuv", f"{avg_attendance}%", "Jamoa intizomi", "green"),
            ("Faol bloklar", len(Training.TYPE_CHOICES), "Turli yonalishlar", "purple"),
        ]
        return context


@method_decorator(login_required, name="dispatch")
class TrainingCreateView(CreateView):
    model = Training
    form_class = TrainingForm
    template_name = "training/form.html"
    success_url = reverse_lazy("training_list")

    def form_valid(self, form):
        messages.success(self.request, "Mashgulot muvaffaqiyatli qo'shildi.")
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class TrainingUpdateView(UpdateView):
    model = Training
    form_class = TrainingForm
    template_name = "training/form.html"
    success_url = reverse_lazy("training_list")

    def form_valid(self, form):
        messages.success(self.request, "Mashgulot ma'lumotlari yangilandi.")
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class TrainingDeleteView(DeleteView):
    model = Training
    template_name = "training/confirm_delete.html"
    success_url = reverse_lazy("training_list")


@method_decorator(login_required, name="dispatch")
class TrainingAttendanceView(TemplateView):
    template_name = "attendance/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trainings = list(Training.objects.order_by("-training_date", "-start_time"))
        selected_training = trainings[0] if trainings else None
        team_stats = calculate_team_attendance_stats()
        player_stats = team_stats["player_stats"]
        chart_rows = [item for item in player_stats if item["total_marked_trainings"]]
        context["trainings"] = trainings
        context["selected_training"] = selected_training
        context["players"] = Player.objects.all()
        context["attendance_status_choices"] = TrainingAttendance.STATUS_CHOICES
        context["injury_status_choices"] = TrainingAttendance.INJURY_CHOICES
        context["fatigue_levels"] = range(1, 6)
        context["activity_scores"] = range(1, 11)
        context["team_stats"] = team_stats
        context["player_stats"] = player_stats
        context["attendance_charts"] = {
            "labels": [item["player_name"] for item in chart_rows],
            "attendance": [item["attendance_percent"] for item in chart_rows],
            "ratings": [item["overall_activity_rating"] for item in chart_rows],
            "statusLabels": list(team_stats["status_counts"].keys()),
            "statusValues": list(team_stats["status_counts"].values()),
        }
        return context


def _json_ok(data=None, message="So'rov muvaffaqiyatli bajarildi."):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    return JsonResponse(payload)


def _json_error(message, status=400, errors=None):
    payload = {"success": False, "message": message}
    if errors:
        payload["errors"] = errors
    return JsonResponse(payload, status=status)


def _parse_json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return None


def _validation_error_messages(error):
    if hasattr(error, "message_dict"):
        return error.message_dict
    return {"xatolik": error.messages}


def _int_value(value, field_label):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError({field_label: f"{field_label} butun son bo'lishi kerak."})


def _record_values_from_payload(payload, training, existing_record=None):
    existing_duration = (
        existing_record.training_duration_minutes
        if existing_record and existing_record.pk
        else get_training_duration_minutes(training)
    )
    existing_minutes = existing_record.attended_minutes if existing_record else existing_duration
    existing_fatigue = existing_record.fatigue_level if existing_record else 1
    existing_activity = existing_record.activity_score if existing_record else 7
    duration = _int_value(
        payload.get("training_duration_minutes", existing_duration) or existing_duration,
        "training_duration_minutes",
    )
    attended_minutes = _int_value(payload.get("attended_minutes", existing_minutes), "attended_minutes")
    fatigue_level = _int_value(payload.get("fatigue_level", existing_fatigue), "fatigue_level")
    activity_score = _int_value(payload.get("activity_score", existing_activity), "activity_score")
    attendance_status = payload.get(
        "attendance_status",
        existing_record.attendance_status if existing_record else TrainingAttendance.STATUS_PRESENT,
    )
    injury_status = payload.get(
        "injury_status",
        existing_record.injury_status if existing_record else TrainingAttendance.INJURY_NO,
    )
    if attendance_status not in dict(TrainingAttendance.STATUS_CHOICES):
        raise ValidationError({"attendance_status": "Davomad holati noto'g'ri yuborildi."})
    if injury_status not in dict(TrainingAttendance.INJURY_CHOICES):
        raise ValidationError({"injury_status": "Jarohat holati noto'g'ri yuborildi."})
    return {
        "attendance_status": attendance_status,
        "attended_minutes": attended_minutes,
        "training_duration_minutes": duration,
        "fatigue_level": fatigue_level,
        "activity_score": activity_score,
        "injury_status": injury_status,
        "coach_note": (
            payload.get(
                "coach_note",
                existing_record.coach_note if existing_record else "",
            )
            or ""
        ).strip(),
    }


@login_required
def attendance_records_api(request):
    if request.method != "GET":
        return _json_error("Bu API uchun noto'g'ri so'rov turi yuborildi.", status=405)
    records = TrainingAttendance.objects.select_related("training", "player").all()
    return _json_ok(
        {"records": [serialize_attendance(record) for record in records]},
        "Davomad va faollik yozuvlari yuklandi.",
    )


@login_required
def training_attendance_api(request, training_id):
    if request.method != "GET":
        return _json_error("Bu API uchun noto'g'ri so'rov turi yuborildi.", status=405)
    training = Training.objects.filter(pk=training_id).first()
    if not training:
        return _json_error("Noto'g'ri mashg'ulot ID yuborildi.", status=404)
    records = {
        record.player_id: serialize_attendance(record)
        for record in TrainingAttendance.objects.filter(training=training).select_related("training", "player")
    }
    rows = []
    for player in Player.objects.all():
        row = records.get(player.id)
        if not row:
            row = build_default_record(player, training)
        rows.append(row)
    return _json_ok(
        {
            "training": serialize_training(training),
            "records": rows,
            "status_choices": [label for _, label in TrainingAttendance.STATUS_CHOICES],
            "injury_choices": [label for _, label in TrainingAttendance.INJURY_CHOICES],
        },
        "Mashg'ulot davomadi yuklandi.",
    )


@login_required
def player_attendance_api(request, player_id):
    if request.method != "GET":
        return _json_error("Bu API uchun noto'g'ri so'rov turi yuborildi.", status=405)
    player = Player.objects.filter(pk=player_id).first()
    if not player:
        return _json_error("Noto'g'ri futbolchi ID yuborildi.", status=404)
    records = list(
        TrainingAttendance.objects.filter(player=player).select_related("training", "player")
    )
    return _json_ok(
        {
            "player": serialize_player(player),
            "history": [serialize_attendance(record) for record in records],
            "statistics": calculate_player_attendance_stats(player, records),
        },
        "Futbolchi mashg'ulot tarixi yuklandi.",
    )


@login_required
def save_training_attendance_api(request, training_id):
    if request.method != "POST":
        return _json_error("Bu API uchun noto'g'ri so'rov turi yuborildi.", status=405)
    payload = _parse_json_body(request)
    if payload is None:
        return _json_error("Ma'lumotlarni saqlashda xatolik yuz berdi", errors={"json": ["JSON noto'g'ri yuborildi."]})
    training = Training.objects.filter(pk=training_id).first()
    if not training:
        return _json_error("Noto'g'ri mashg'ulot ID yuborildi.", status=404)
    records_payload = payload.get("records", [])
    if not records_payload:
        return _json_error("Hozircha ma'lumot mavjud emas")

    saved_records = []
    for item in records_payload:
        player_id = item.get("player_id") or item.get("player", {}).get("id")
        if not player_id:
            return _json_error("Noto'g'ri futbolchi ID yuborildi.", errors={"player_id": ["Futbolchi tanlanmagan."]})
        player = Player.objects.filter(pk=player_id).first()
        if not player:
            return _json_error("Noto'g'ri futbolchi ID yuborildi.", status=404)
        try:
            record = TrainingAttendance.objects.filter(training=training, player=player).first()
            if record is None:
                record = TrainingAttendance(training=training, player=player)
            values = _record_values_from_payload(item, training, record)
            for field, value in values.items():
                setattr(record, field, value)
            record.full_clean()
            record.save()
        except ValidationError as error:
            return _json_error(
                "Ma'lumotlarni saqlashda xatolik yuz berdi",
                errors=_validation_error_messages(error),
            )
        saved_records.append(serialize_attendance(record))

    present_count = TrainingAttendance.objects.filter(
        training=training,
        attendance_status=TrainingAttendance.STATUS_PRESENT,
    ).count()
    total_count = TrainingAttendance.objects.filter(training=training).count()
    Training.objects.filter(pk=training.pk).update(
        attendance_present=present_count,
        attendance_total=total_count,
    )
    return _json_ok(
        {"records": saved_records, "team_stats": calculate_team_attendance_stats()},
        "Ma'lumotlar muvaffaqiyatli saqlandi",
    )


@login_required
def attendance_record_detail_api(request, record_id):
    record = TrainingAttendance.objects.select_related("training", "player").filter(pk=record_id).first()
    if not record:
        return _json_error("Davomad yozuvi topilmadi.", status=404)
    if request.method == "GET":
        return _json_ok({"record": serialize_attendance(record)}, "Davomad yozuvi yuklandi.")
    if request.method in {"PUT", "PATCH"}:
        payload = _parse_json_body(request)
        if payload is None:
            return _json_error("Ma'lumotlarni saqlashda xatolik yuz berdi", errors={"json": ["JSON noto'g'ri yuborildi."]})
        try:
            values = _record_values_from_payload(payload, record.training, record)
            for field, value in values.items():
                setattr(record, field, value)
            record.full_clean()
            record.save()
        except ValidationError as error:
            return _json_error(
                "Ma'lumotlarni saqlashda xatolik yuz berdi",
                errors=_validation_error_messages(error),
            )
        return _json_ok({"record": serialize_attendance(record)}, "Davomad yozuvi yangilandi.")
    if request.method == "DELETE":
        record.delete()
        return _json_ok(message="Davomad yozuvi o'chirildi.")
    return _json_error("Bu API uchun noto'g'ri so'rov turi yuborildi.", status=405)


@login_required
def team_attendance_stats_api(request):
    if request.method != "GET":
        return _json_error("Bu API uchun noto'g'ri so'rov turi yuborildi.", status=405)
    return _json_ok(calculate_team_attendance_stats(), "Umumiy jamoa statistikasi yuklandi.")


@login_required
def players_attendance_stats_api(request):
    if request.method != "GET":
        return _json_error("Bu API uchun noto'g'ri so'rov turi yuborildi.", status=405)
    return _json_ok({"players": calculate_all_player_stats()}, "Futbolchilar statistikasi yuklandi.")


@method_decorator(login_required, name="dispatch")
class StatisticsView(TemplateView):
    template_name = "statistics/index.html"

    FILTER_OPTIONS = {
        "7d": "So'nggi 7 kun",
        "30d": "So'nggi 30 kun",
        "season": "Joriy mavsum",
    }
    MONTH_LABELS = {
        1: "Yan",
        2: "Fev",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Iyn",
        7: "Iyl",
        8: "Avg",
        9: "Sen",
        10: "Okt",
        11: "Noy",
        12: "Dek",
    }

    @staticmethod
    def _build_sparkline(values, width=120, height=34, padding_x=4, padding_y=5):
        if not values:
            return ""
        max_value = max(values) or 1
        step_x = (width - padding_x * 2) / max(len(values) - 1, 1)
        points = []
        for index, value in enumerate(values):
            x_pos = padding_x + (step_x * index)
            y_pos = height - padding_y - ((value / max_value) * (height - padding_y * 2))
            points.append(f"{round(x_pos, 2)},{round(y_pos, 2)}")
        return " ".join(points)

    @staticmethod
    def _build_sparkline_meta(values, width=142, height=54, padding_x=8, padding_y=8):
        if not values:
            return {
                "points": "",
                "area": "",
                "last_x": 0,
                "last_y": 0,
            }
        min_value = min(values)
        max_value = max(values)
        value_range = max(max_value - min_value, 1)
        step_x = (width - padding_x * 2) / max(len(values) - 1, 1)
        point_pairs = []
        for index, value in enumerate(values):
            x_pos = padding_x + (step_x * index)
            y_pos = height - padding_y - (((value - min_value) / value_range) * (height - padding_y * 2))
            point_pairs.append((round(x_pos, 2), round(y_pos, 2)))
        points = " ".join(f"{x_pos},{y_pos}" for x_pos, y_pos in point_pairs)
        area = (
            f"{padding_x},{height - padding_y} "
            f"{points} "
            f"{width - padding_x},{height - padding_y}"
        )
        last_x, last_y = point_pairs[-1]
        return {
            "points": points,
            "area": area,
            "last_x": last_x,
            "last_y": last_y,
        }

    @staticmethod
    def _build_kpi_series(current_value, spread=6, steps=8, minimum=0):
        current_value = int(current_value or 0)
        start_value = max(current_value - spread, minimum)
        if steps <= 1:
            return [current_value]
        return [
            round(start_value + ((current_value - start_value) * index / (steps - 1)))
            for index in range(steps)
        ]

    @staticmethod
    def _build_chart_points(values, width=640, height=260, padding_x=28, padding_y=22):
        if not values:
            return ""
        max_value = max(values) or 1
        step_x = (width - padding_x * 2) / max(len(values) - 1, 1)
        points = []
        for index, value in enumerate(values):
            x_pos = padding_x + (step_x * index)
            y_pos = height - padding_y - ((value / max_value) * (height - padding_y * 2))
            points.append(f"{round(x_pos, 2)},{round(y_pos, 2)}")
        return " ".join(points)

    @staticmethod
    def _polar_to_cartesian(cx, cy, radius, angle):
        import math

        angle_rad = (angle - 90) * math.pi / 180
        return cx + (radius * math.cos(angle_rad)), cy + (radius * math.sin(angle_rad))

    @classmethod
    def _build_donut_segments(cls, items):
        total = sum(item["value"] for item in items) or 1
        start_angle = 0
        segments = []
        for item in items:
            sweep = (item["value"] / total) * 360
            end_angle = start_angle + sweep
            start_x, start_y = cls._polar_to_cartesian(80, 80, 56, start_angle)
            end_x, end_y = cls._polar_to_cartesian(80, 80, 56, end_angle)
            large_arc = 1 if sweep > 180 else 0
            path = (
                f"M {start_x:.2f} {start_y:.2f} "
                f"A 56 56 0 {large_arc} 1 {end_x:.2f} {end_y:.2f}"
            )
            item["path"] = path
            item["percentage"] = round((item["value"] / total) * 100)
            segments.append(item)
            start_angle = end_angle
        return segments

    @staticmethod
    def _safe_div(numerator, denominator):
        return round((numerator / denominator) * 100) if denominator else 0

    @staticmethod
    def _format_match_result(match):
        if not match:
            return "-"
        return f"{match.home_team} {match.home_score}:{match.away_score} {match.away_team}"

    def _get_reference_date(self):
        scored_matches = Match.objects.exclude(home_score__isnull=True).exclude(away_score__isnull=True)
        latest_match = scored_matches.order_by("-match_date").first() or Match.objects.order_by("-match_date").first()
        return latest_match.match_date if latest_match else date.today()

    def _get_filtered_matches(self, selected_filter):
        queryset = Match.objects.order_by("match_date", "match_time")
        reference_date = self._get_reference_date()
        if selected_filter == "7d":
            start_date = reference_date - timedelta(days=6)
            queryset = queryset.filter(match_date__range=(start_date, reference_date))
        elif selected_filter == "30d":
            start_date = reference_date - timedelta(days=29)
            queryset = queryset.filter(match_date__range=(start_date, reference_date))
        return list(queryset), reference_date

    def _build_period_series(self, matches, selected_filter):
        completed_matches = [match for match in matches if match.home_score is not None and match.away_score is not None]
        if not completed_matches:
            return {
                "labels": [],
                "goals": [],
                "assists": [],
                "goals_points": "",
                "assists_points": "",
                "goal_total": 0,
                "assist_total": 0,
                "best_label": "-",
                "best_value": 0,
                "average_goals": "0",
            }

        if selected_filter == "7d":
            series_matches = completed_matches[-7:]
        elif selected_filter == "30d":
            series_matches = completed_matches[-8:]
        else:
            series_matches = completed_matches[-8:]

        labels = [f"{match.match_date.day:02d} {self.MONTH_LABELS[match.match_date.month]}" for match in series_matches]
        goals = [(match.home_score or 0) + (match.away_score or 0) for match in series_matches]
        assists = [max(goals_item - 1, 0) for goals_item in goals]
        best_index = goals.index(max(goals)) if goals else 0

        return {
            "labels": labels,
            "goals": goals,
            "assists": assists,
            "goals_points": self._build_chart_points(goals),
            "assists_points": self._build_chart_points(assists),
            "goal_total": sum(goals),
            "assist_total": sum(assists),
            "best_label": labels[best_index] if labels else "-",
            "best_value": goals[best_index] if goals else 0,
            "average_goals": f"{(sum(goals) / len(goals)):.1f}" if goals else "0",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = list(PlayerStatistic.objects.select_related("player"))
        top_stats = sorted(
            stats,
            key=lambda item: (item.rating, item.goals + item.assists, item.goals),
            reverse=True,
        )
        selected_filter = self.request.GET.get("range", "season")
        if selected_filter not in self.FILTER_OPTIONS:
            selected_filter = "season"

        filtered_matches, reference_date = self._get_filtered_matches(selected_filter)
        completed_matches = [
            match for match in filtered_matches
            if match.home_score is not None and match.away_score is not None
        ]
        played_matches = [match for match in completed_matches if match.status == Match.STATUS_PLAYED]
        wins = sum(1 for match in completed_matches if (match.home_score or 0) > (match.away_score or 0))
        draws = sum(1 for match in completed_matches if (match.home_score or 0) == (match.away_score or 0))
        losses = sum(1 for match in completed_matches if (match.home_score or 0) < (match.away_score or 0))
        matches_count = len(filtered_matches)
        completed_count = len(completed_matches)
        points = wins * 3 + draws
        points_per_match = points / completed_count if completed_count else 0
        goals_for = sum(match.home_score or 0 for match in completed_matches)
        goals_against = sum(match.away_score or 0 for match in completed_matches)
        goal_difference = goals_for - goals_against
        best_win = max(
            completed_matches,
            key=lambda match: (match.home_score or 0) - (match.away_score or 0),
            default=None,
        )
        toughest_result = min(
            completed_matches,
            key=lambda match: (match.home_score or 0) - (match.away_score or 0),
            default=None,
        )
        recent_form = []
        for match in completed_matches[-5:]:
            if (match.home_score or 0) > (match.away_score or 0):
                recent_form.append({"label": "G", "tone": "win"})
            elif (match.home_score or 0) == (match.away_score or 0):
                recent_form.append({"label": "D", "tone": "draw"})
            else:
                recent_form.append({"label": "M", "tone": "loss"})
        line_chart = self._build_period_series(filtered_matches, selected_filter)
        total_goals = line_chart["goal_total"]
        total_assists = line_chart["assist_total"]
        player_total = Player.objects.count()
        win_rate = self._safe_div(wins, completed_count)
        range_spreads = {
            "7d": {"matches": 3, "goals": 6, "win_rate": 8},
            "30d": {"matches": 5, "goals": 9, "win_rate": 10},
            "season": {"matches": 7, "goals": 12, "win_rate": 12},
        }
        kpi_series = {
            "players": self._build_kpi_series(player_total, spread=2),
            "matches": self._build_kpi_series(matches_count, spread=range_spreads[selected_filter]["matches"]),
            "goals": self._build_kpi_series(total_goals, spread=range_spreads[selected_filter]["goals"]),
            "win_rate": self._build_kpi_series(win_rate, spread=range_spreads[selected_filter]["win_rate"]),
        }

        trend_map = {
            "7d": {
                "players": "+1 yangi futbolchi",
                "matches": f"{completed_count} ta yakunlangan o'yin",
                "goals": f"{total_assists} ta golli uzatma bilan bog'liq",
                "win_rate": f"{reference_date.day:02d} {self.MONTH_LABELS[reference_date.month]} gacha",
            },
            "30d": {
                "players": "Asosiy tarkib barqaror",
                "matches": f"{completed_count} ta natijali o'yin",
                "goals": f"{total_goals} ta umumiy gol",
                "win_rate": "Oxirgi oy formasi",
            },
            "season": {
                "players": "+2 yangi tarkib",
                "matches": f"{completed_count} ta statistik o'yin",
                "goals": f"{total_goals} ta hujum samarasi",
                "win_rate": "Joriy mavsum ko'rsatkichi",
            },
        }

        kpi_cards = [
            {
                "title": "Jami futbolchilar",
                "value": player_total,
                "trend_text": trend_map[selected_filter]["players"],
                "trend_direction": "up",
                "icon": "bi-people-fill",
                "accent": "blue",
                "sparkline": self._build_sparkline_meta(kpi_series["players"]),
            },
            {
                "title": "O'yinlar soni",
                "value": matches_count,
                "trend_text": trend_map[selected_filter]["matches"],
                "trend_direction": "up",
                "icon": "bi-trophy-fill",
                "accent": "cyan",
                "sparkline": self._build_sparkline_meta(kpi_series["matches"]),
            },
            {
                "title": "Gollar",
                "value": total_goals,
                "trend_text": trend_map[selected_filter]["goals"],
                "trend_direction": "up",
                "icon": "bi-bullseye",
                "accent": "green",
                "sparkline": self._build_sparkline_meta(kpi_series["goals"]),
            },
            {
                "title": "G'alaba foizi",
                "value": f"{win_rate}%",
                "trend_text": trend_map[selected_filter]["win_rate"],
                "trend_direction": "up" if win_rate >= 50 else "down",
                "icon": "bi-graph-up-arrow",
                "accent": "purple",
                "sparkline": self._build_sparkline_meta(kpi_series["win_rate"]),
            },
        ]
        donut_segments = self._build_donut_segments(
            [
                {"label": "G'alaba", "value": wins, "color": "#22C55E", "tone": "win", "icon": "bi-trophy-fill"},
                {"label": "Durang", "value": draws, "color": "#3B82F6", "tone": "draw", "icon": "bi-dash-circle-fill"},
                {"label": "Mag'lubiyat", "value": losses, "color": "#8B5CF6", "tone": "loss", "icon": "bi-shield-fill-x"},
            ]
        )
        donut_total = sum(item["value"] for item in donut_segments)
        result_summary = {
            "record": f"{wins}-{draws}-{losses}",
            "points": points,
            "points_per_match": f"{points_per_match:.2f}",
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_difference": f"{goal_difference:+d}",
            "best_result": self._format_match_result(best_win) if best_win and (best_win.home_score or 0) > (best_win.away_score or 0) else "-",
            "toughest_result": self._format_match_result(toughest_result) if toughest_result else "-",
            "form": recent_form,
            "win_rate": win_rate,
        }

        top_player_cards = top_stats[:4]
        rating_rows = top_stats[:8]
        rating_max = max((float(item.rating) for item in rating_rows), default=10)
        for row in rating_rows:
            row.form_percent = round((float(row.rating) / rating_max) * 100) if rating_max else 0
        statistics_charts = {
            "selectedLabel": self.FILTER_OPTIONS[selected_filter],
            "attack": {
                "labels": line_chart["labels"],
                "goals": line_chart["goals"],
                "assists": line_chart["assists"],
                "totals": [goal + assist for goal, assist in zip(line_chart["goals"], line_chart["assists"])],
                "goalTotal": total_goals,
                "assistTotal": total_assists,
                "averageGoals": line_chart["average_goals"],
                "bestLabel": line_chart["best_label"],
                "bestValue": line_chart["best_value"],
            },
            "results": {
                "labels": [item["label"] for item in donut_segments],
                "values": [item["value"] for item in donut_segments],
                "colors": [item["color"] for item in donut_segments],
                "total": donut_total,
                "winRate": win_rate,
            },
        }

        context["statistics_filters"] = [
            {"key": key, "label": label, "active": key == selected_filter}
            for key, label in self.FILTER_OPTIONS.items()
        ]
        context["selected_filter"] = selected_filter
        context["selected_filter_label"] = self.FILTER_OPTIONS[selected_filter]
        context["kpi_cards"] = kpi_cards
        context["top_player_cards"] = top_player_cards
        context["rating_rows"] = rating_rows
        context["line_chart"] = line_chart
        context["donut_segments"] = donut_segments
        context["donut_total"] = donut_total
        context["result_summary"] = result_summary
        context["statistics_charts"] = statistics_charts
        return context


@method_decorator(login_required, name="dispatch")
class SettingsView(TemplateView):
    template_name = "settings/index.html"

    def _get_profile(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def _build_context(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self._get_profile()
        coach_profile = getattr(self.request.user, "coach_profile", None)
        context["profile"] = profile
        context["coach_profile"] = coach_profile
        context["settings_form"] = kwargs.get(
            "settings_form",
            UserSettingsForm(
                instance=profile,
                user=self.request.user,
                coach_profile=coach_profile,
            ),
        )
        context["password_form"] = kwargs.get(
            "password_form",
            StyledPasswordChangeForm(user=self.request.user),
        )
        context["settings_menu"] = [
            ("profile", "Profil"),
            ("account", "Hisob"),
            ("security", "Xavfsizlik"),
            ("notifications", "Bildirishnomalar"),
            ("system", "Tizim sozlamalari"),
        ]
        return context

    def get_context_data(self, **kwargs):
        return self._build_context(**kwargs)

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get("form_type", "settings")
        profile = self._get_profile()
        coach_profile = getattr(self.request.user, "coach_profile", None)
        if form_type == "password":
            password_form = StyledPasswordChangeForm(user=request.user, data=request.POST)
            settings_form = UserSettingsForm(
                instance=profile,
                user=request.user,
                coach_profile=coach_profile,
            )
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Parol muvaffaqiyatli yangilandi.")
                return redirect("settings")
            messages.error(request, "Parolni yangilashda xatolik bor.")
            return self.render_to_response(
                self._build_context(settings_form=settings_form, password_form=password_form)
            )

        settings_form = UserSettingsForm(
            request.POST,
            request.FILES,
            instance=profile,
            user=request.user,
            coach_profile=coach_profile,
        )
        password_form = StyledPasswordChangeForm(user=request.user)
        if settings_form.is_valid():
            saved_profile = settings_form.save()
            language = settings_form.cleaned_data["language"]
            request.session["django_language"] = language
            activate(language)
            request.session["theme"] = saved_profile.theme
            messages.success(request, "Sozlamalar saqlandi.")
            return redirect("settings")
        messages.error(request, "Sozlamalarni saqlashda xatolik bor.")
        return self.render_to_response(
            self._build_context(settings_form=settings_form, password_form=password_form)
        )
