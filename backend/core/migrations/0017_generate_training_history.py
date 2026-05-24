from datetime import date, timedelta, time

from django.db import migrations


TRAINING_TYPES = ["tactics", "fitness", "technical", "recovery"]
TRAINING_TITLES = [
    "Pressing va himoya bloki",
    "Tezkor hujumlar",
    "Standart vaziyatlar",
    "Tiklanish va monitoring",
    "Yakuniy paslar",
    "Jismoniy yuklama",
]
STATUS_PRESENT = "Qatnashdi"
STATUS_ABSENT = "Qatnashmadi"
INJURY_NO = "Yo'q"
PHYSICAL_GOOD = "good"
PHYSICAL_TIRED = "tired"
ACTIVITY_MEDIUM = "medium"
ACTIVITY_HIGH = "high"
DISCIPLINE_GOOD = "good"


def generate_training_history(apps, schema_editor):
    Player = apps.get_model("core", "Player")
    Training = apps.get_model("core", "Training")
    TrainingAttendance = apps.get_model("core", "TrainingAttendance")
    players = list(Player.objects.order_by("shirt_number", "full_name"))
    if not players:
        return

    for index in range(100):
        training_date = date(2026, 5, 25) - timedelta(days=index)
        start_hour = 9 + (index % 3)
        duration = 75 + (index % 4) * 15
        start_time = time(start_hour, 0)
        end_time = time(start_hour + duration // 60, duration % 60)
        title = f"{TRAINING_TITLES[index % len(TRAINING_TITLES)]} #{index + 1}"
        training, _ = Training.objects.update_or_create(
            title=title,
            training_date=training_date,
            defaults={
                "training_type": TRAINING_TYPES[index % len(TRAINING_TYPES)],
                "start_time": start_time,
                "end_time": end_time,
                "location": "Bunyodkor akademiyasi",
                "note": "Demo davr grafiklari uchun avtomatik mashg'ulot.",
                "attendance_total": len(players),
                "attendance_present": 0,
            },
        )

        present_count = 0
        for player_index, player in enumerate(players):
            absent = (player_index + index) % 13 == 0
            status = STATUS_ABSENT if absent else STATUS_PRESENT
            if not absent:
                present_count += 1
            rating = 6 + ((player_index + index) % 5)
            activity_score = 5 + ((player_index * 2 + index) % 6)
            TrainingAttendance.objects.update_or_create(
                training=training,
                player=player,
                defaults={
                    "attendance_status": status,
                    "physical_condition": PHYSICAL_TIRED if index % 11 == 0 else PHYSICAL_GOOD,
                    "activity_level": ACTIVITY_HIGH if activity_score >= 8 else ACTIVITY_MEDIUM,
                    "discipline": DISCIPLINE_GOOD,
                    "rating": rating,
                    "attended_minutes": 0 if absent else duration,
                    "training_duration_minutes": duration,
                    "fatigue_level": 2 + (index + player_index) % 5,
                    "pain_level": 1 + (index + player_index) % 3,
                    "sleep_quality": 6 + (player_index + index) % 4,
                    "activity_score": 1 if absent else activity_score,
                    "injury_status": INJURY_NO,
                    "coach_note": "Demo mashg'ulot baholash yozuvi.",
                },
            )
        training.attendance_present = present_count
        training.save(update_fields=["attendance_present", "attendance_total"])


def remove_training_history(apps, schema_editor):
    Training = apps.get_model("core", "Training")
    Training.objects.filter(note="Demo davr grafiklari uchun avtomatik mashg'ulot.").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0016_generate_match_history"),
    ]

    operations = [
        migrations.RunPython(generate_training_history, remove_training_history),
    ]
