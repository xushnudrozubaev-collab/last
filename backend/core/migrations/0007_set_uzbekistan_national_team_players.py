from datetime import date

from django.db import migrations


PLAYERS = [
    (1, "O\u2018tkir Yusupov", "goalkeeper", "Darvozabon", 18, 1, 2, "7.8"),
    (2, "Abduqodir Husanov", "defender", "Himoyachi", 20, 2, 1, "8.0"),
    (3, "Hojiakbar Alijonov", "defender", "Himoyachi", 19, 1, 4, "7.7"),
    (4, "Sherzod Nasrullayev", "defender", "Himoyachi", 17, 1, 3, "7.6"),
    (5, "Husniddin Aliqulov", "defender", "Himoyachi", 21, 3, 2, "7.9"),
    (6, "Akmal Mozgovoy", "midfielder", "Yarim himoyachi", 22, 4, 5, "8.1"),
    (7, "Odiljon Hamrobekov", "midfielder", "Yarim himoyachi", 23, 3, 6, "8.2"),
    (8, "Eldor Shomurodov", "forward", "Hujumchi", 24, 9, 4, "8.6"),
    (9, "Abbosbek Fayzullayev", "midfielder", "Yarim himoyachi", 23, 7, 8, "8.7"),
    (10, "Jaloliddin Masharipov", "midfielder", "Yarim himoyachi / hujumchi", 22, 6, 9, "8.5"),
    (11, "Azizbek Turg\u2018unboyev", "midfielder", "Yarim himoyachi", 18, 5, 4, "8.0"),
]


def set_national_team_players(apps, schema_editor):
    Player = apps.get_model("core", "Player")
    PlayerStatistic = apps.get_model("core", "PlayerStatistic")

    Player.objects.all().delete()
    for shirt_number, full_name, position, role_note, matches, goals, assists, rating in PLAYERS:
        player = Player.objects.create(
            full_name=full_name,
            shirt_number=shirt_number,
            position=position,
            age=25,
            nationality="O'zbekiston",
            height="1.80",
            weight=75,
            join_date=date(2026, 1, 1),
            photo="",
            short_note=f"O'zbekiston milliy terma jamoasi futbolchisi. Roli: {role_note}.",
        )
        PlayerStatistic.objects.create(
            player=player,
            matches_played=matches,
            goals=goals,
            assists=assists,
            rating=rating,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_alter_trainingattendance_activity_score_and_more"),
    ]

    operations = [
        migrations.RunPython(set_national_team_players, migrations.RunPython.noop),
    ]
