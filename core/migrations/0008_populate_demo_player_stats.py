from datetime import date, time

from django.db import migrations


PLAYER_STATS = {
    "O\u2018tkir Yusupov": (18, 1, 2, "7.8"),
    "Abduqodir Husanov": (20, 2, 1, "8.0"),
    "Hojiakbar Alijonov": (19, 1, 4, "7.7"),
    "Sherzod Nasrullayev": (17, 1, 3, "7.6"),
    "Husniddin Aliqulov": (21, 3, 2, "7.9"),
    "Akmal Mozgovoy": (22, 4, 5, "8.1"),
    "Odiljon Hamrobekov": (23, 3, 6, "8.2"),
    "Eldor Shomurodov": (24, 9, 4, "8.6"),
    "Abbosbek Fayzullayev": (23, 7, 8, "8.7"),
    "Jaloliddin Masharipov": (22, 6, 9, "8.5"),
    "Azizbek Turg\u2018unboyev": (18, 5, 4, "8.0"),
}

STATUS_PRESENT = "Qatnashdi"
STATUS_LATE = "Kechikdi"
STATUS_EXCUSED = "Uzrli sabab"
INJURY_NO = "Yo'q"
INJURY_RECOVERING = "Tiklanmoqda"

TRAININGS = [
    ("Pressing va tezkor o'tish", "tactics", date(2026, 5, 16), time(9, 0), time(10, 30), "Bunyodkor akademiyasi"),
    ("Zarba va yakuniy paslar", "technical", date(2026, 5, 17), time(9, 30), time(11, 0), "Jar stadioni"),
    ("Tiklanish va forma nazorati", "recovery", date(2026, 5, 18), time(10, 0), time(11, 15), "Milliy jamoa bazasi"),
]


def populate_demo_player_stats(apps, schema_editor):
    Player = apps.get_model("core", "Player")
    PlayerStatistic = apps.get_model("core", "PlayerStatistic")
    Training = apps.get_model("core", "Training")
    TrainingAttendance = apps.get_model("core", "TrainingAttendance")

    for player in Player.objects.all():
        matches, goals, assists, rating = PLAYER_STATS.get(
            player.full_name,
            (16 + (player.shirt_number % 8), 1 + (player.shirt_number % 4), 1 + (player.shirt_number % 5), "7.5"),
        )
        PlayerStatistic.objects.update_or_create(
            player=player,
            defaults={
                "matches_played": matches,
                "goals": goals,
                "assists": assists,
                "rating": rating,
            },
        )

    trainings = []
    for title, training_type, training_date, start_time, end_time, location in TRAININGS:
        training, _ = Training.objects.update_or_create(
            title=title,
            training_date=training_date,
            defaults={
                "training_type": training_type,
                "start_time": start_time,
                "end_time": end_time,
                "location": location,
                "attendance_total": Player.objects.count(),
                "attendance_present": Player.objects.count(),
                "note": "Demo statistikalar uchun avtomatik mashg'ulot.",
            },
        )
        trainings.append(training)

    players = list(Player.objects.order_by("shirt_number", "full_name"))
    for training_index, training in enumerate(trainings):
        duration = max(
            (training.end_time.hour * 60 + training.end_time.minute)
            - (training.start_time.hour * 60 + training.start_time.minute),
            75,
        )
        present_count = 0
        for player_index, player in enumerate(players):
            status = STATUS_PRESENT
            minutes = duration
            if (player_index + training_index) % 7 == 0:
                status = STATUS_LATE
                minutes = max(duration - 12, 1)
            elif (player_index + training_index) % 11 == 0:
                status = STATUS_EXCUSED
                minutes = max(duration - 25, 1)
            if status in {STATUS_PRESENT, STATUS_LATE}:
                present_count += 1

            TrainingAttendance.objects.update_or_create(
                training=training,
                player=player,
                defaults={
                    "attendance_status": status,
                    "attended_minutes": minutes,
                    "training_duration_minutes": duration,
                    "fatigue_level": 2 + ((player_index + training_index) % 3),
                    "activity_score": 7 + ((player_index + training_index) % 4),
                    "injury_status": INJURY_RECOVERING
                    if (player_index + training_index) % 13 == 0
                    else INJURY_NO,
                    "coach_note": "Demo baholash: forma va ishtirok ko'rsatkichlari to'ldirilgan.",
                },
            )
        training.attendance_total = len(players)
        training.attendance_present = present_count
        training.save(update_fields=["attendance_total", "attendance_present"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_set_uzbekistan_national_team_players"),
    ]

    operations = [
        migrations.RunPython(populate_demo_player_stats, migrations.RunPython.noop),
    ]
