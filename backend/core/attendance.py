from datetime import date
from statistics import mean

from .models import Player, Training, TrainingAttendance


ACTIVE_STATUSES = {
    TrainingAttendance.STATUS_PRESENT,
}


def round_percent(value):
    return round(float(value or 0), 2)


def get_training_duration_minutes(training):
    if not training:
        return 90
    start_minutes = training.start_time.hour * 60 + training.start_time.minute
    end_minutes = training.end_time.hour * 60 + training.end_time.minute
    duration = end_minutes - start_minutes
    return duration if duration > 0 else 90


def serialize_training(training):
    return {
        "id": training.id,
        "title": training.title,
        "date": training.training_date.isoformat(),
        "date_display": training.training_date.strftime("%d.%m.%Y"),
        "type": training.get_training_type_display(),
        "start_time": training.start_time.strftime("%H:%M"),
        "end_time": training.end_time.strftime("%H:%M"),
        "duration_minutes": get_training_duration_minutes(training),
        "duration_display": training.duration_display,
        "location": training.location,
    }


def serialize_player(player):
    return {
        "id": player.id,
        "full_name": player.full_name,
        "position": player.get_position_display(),
        "shirt_number": player.shirt_number,
        "photo_url": player.photo_display_url if player.photo else "",
        "initials": player.initials,
    }


def serialize_attendance(record):
    return {
        "id": record.id,
        "training": serialize_training(record.training),
        "player": serialize_player(record.player),
        "attendance_status": record.attendance_status,
        "attendance_status_display": record.get_attendance_status_display(),
        "physical_condition": record.physical_condition,
        "physical_condition_display": record.get_physical_condition_display(),
        "activity_level": record.activity_level,
        "activity_level_display": record.get_activity_level_display(),
        "discipline": record.discipline,
        "discipline_display": record.get_discipline_display(),
        "rating": record.rating,
        "attended_minutes": record.attended_minutes,
        "training_duration_minutes": record.training_duration_minutes,
        "participation_percent": record.participation_percent,
        "fatigue_level": record.fatigue_level,
        "pain_level": record.pain_level,
        "sleep_quality": record.sleep_quality,
        "activity_score": record.activity_score,
        "heart_rate": record.heart_rate,
        "blood_pressure": record.blood_pressure,
        "body_temperature": record.body_temperature,
        "measured_weight": record.measured_weight,
        "measured_height": record.measured_height,
        "oxygen_saturation": record.oxygen_saturation,
        "respiratory_rate": record.respiratory_rate,
        "injury_status": record.injury_status,
        "injury_note": record.injury_note,
        "coach_note": record.coach_note,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
    }


def build_default_record(player, training):
    duration = get_training_duration_minutes(training)
    return {
        "id": None,
        "training_id": training.id,
        "player": serialize_player(player),
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
        "fatigue_level": 1,
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
        "injury_note": "",
        "coach_note": "",
    }


def calculate_player_attendance_stats(player, records=None):
    if records is None:
        records = list(
            TrainingAttendance.objects.filter(player=player).select_related("training", "player")
        )
    else:
        records = list(records)

    total = len(records)
    attended = sum(1 for item in records if item.attendance_status in ACTIVE_STATUSES)
    active_records = [item for item in records if item.attendance_status in ACTIVE_STATUSES]
    absent = sum(1 for item in records if item.attendance_status == TrainingAttendance.STATUS_ABSENT)
    late = sum(1 for item in records if item.attendance_status == TrainingAttendance.STATUS_LATE)
    excused = sum(1 for item in records if item.attendance_status == TrainingAttendance.STATUS_EXCUSED)
    injury_yes = sum(1 for item in records if item.injury_status == TrainingAttendance.INJURY_YES)
    recovering = sum(1 for item in records if item.injury_status == TrainingAttendance.INJURY_RECOVERING)
    attendance_percent = round_percent((attended / total) * 100) if total else 0
    avg_participation = round_percent(mean(item.participation_percent for item in active_records)) if active_records else 0
    avg_minutes = round_percent(mean(item.attended_minutes for item in active_records)) if active_records else 0
    avg_fatigue = round_percent(mean(item.fatigue_level for item in active_records)) if active_records else 0
    avg_heart_rate = round_percent(mean(item.heart_rate for item in active_records if item.heart_rate)) if any(item.heart_rate for item in active_records) else 0
    avg_activity = round_percent(mean(item.activity_score for item in active_records)) if active_records else 0
    avg_rating = round_percent(mean(item.rating for item in active_records)) if active_records else 0
    latest_active = next((item for item in records if item.attendance_status in ACTIVE_STATUSES), None)
    latest_physical_condition = latest_active.get_physical_condition_display() if latest_active else "Kiritilmagan"
    injury_frequency = round_percent(((injury_yes + recovering) / total) * 100) if total else 0
    overall_rating = round_percent(
        (attendance_percent + avg_participation + (avg_rating * 10)) / 3
    ) if total else 0

    return {
        "player_id": player.id,
        "player_name": player.full_name,
        "position": player.get_position_display(),
        "shirt_number": player.shirt_number,
        "total_marked_trainings": total,
        "attended_trainings": attended,
        "absent_trainings": absent,
        "late_trainings": late,
        "excused_trainings": excused,
        "attendance_percent": attendance_percent,
        "average_participation_percent": avg_participation,
        "average_attended_minutes": avg_minutes,
        "average_fatigue_level": avg_fatigue,
        "average_heart_rate": avg_heart_rate,
        "average_activity_score": avg_activity,
        "average_rating": avg_rating,
        "latest_physical_condition": latest_physical_condition,
        "injury_count": injury_yes,
        "recovering_count": recovering,
        "injury_frequency": injury_frequency,
        "overall_activity_rating": overall_rating,
    }


def calculate_all_player_stats():
    records_by_player = {}
    records = TrainingAttendance.objects.select_related("training", "player").all()
    for record in records:
        records_by_player.setdefault(record.player_id, []).append(record)
    return [
        calculate_player_attendance_stats(player, records_by_player.get(player.id, []))
        for player in Player.objects.all()
    ]


def calculate_team_attendance_stats():
    player_stats = calculate_all_player_stats()
    marked_player_stats = [item for item in player_stats if item["total_marked_trainings"]]
    records = list(TrainingAttendance.objects.select_related("training", "player"))
    avg_attendance = round_percent(
        mean(item["attendance_percent"] for item in marked_player_stats)
    ) if marked_player_stats else 0
    avg_activity = round_percent(
        mean(item["average_activity_score"] for item in marked_player_stats)
    ) if marked_player_stats else 0
    avg_rating = round_percent(
        mean(item["average_rating"] for item in marked_player_stats)
    ) if marked_player_stats else 0
    avg_fatigue = round_percent(
        mean(item["average_fatigue_level"] for item in marked_player_stats)
    ) if marked_player_stats else 0
    heart_rate_values = [item["average_heart_rate"] for item in marked_player_stats if item["average_heart_rate"]]
    avg_heart_rate = round_percent(mean(heart_rate_values)) if heart_rate_values else 0
    today_training_ids = set(Training.objects.filter(training_date=date.today()).values_list("id", flat=True))
    today_records = [item for item in records if item.training_id in today_training_ids]
    today_active = sum(1 for item in today_records if item.attendance_status in ACTIVE_STATUSES)
    today_attendance = round_percent((today_active / len(today_records)) * 100) if today_records else 0
    top_player = max(marked_player_stats, key=lambda item: item["overall_activity_rating"], default=None)
    most_absent = max(marked_player_stats, key=lambda item: item["absent_trainings"], default=None)
    status_counts = {
        "Qatnashdi": sum(1 for item in records if item.attendance_status == TrainingAttendance.STATUS_PRESENT),
        "Qatnashmadi": sum(1 for item in records if item.attendance_status == TrainingAttendance.STATUS_ABSENT),
    }
    injury_related = sum(
        1
        for item in records
        if item.injury_status in {TrainingAttendance.INJURY_YES, TrainingAttendance.INJURY_RECOVERING}
    )

    return {
        "total_trainings": Training.objects.count(),
        "total_records": len(records),
        "average_attendance_percent": avg_attendance,
        "average_activity_score": avg_activity,
        "average_rating": avg_rating,
        "average_fatigue_level": avg_fatigue,
        "average_heart_rate": avg_heart_rate,
        "today_attendance_percent": today_attendance,
        "top_player": top_player,
        "most_absent_player": most_absent,
        "injury_related_count": injury_related,
        "status_counts": status_counts,
        "player_stats": player_stats,
    }
