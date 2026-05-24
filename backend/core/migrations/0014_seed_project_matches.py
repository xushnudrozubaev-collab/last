from datetime import date, time

from django.db import migrations


MATCHES = [
    {
        "home_team": "Bunyodkor",
        "away_team": "Paxtakor",
        "match_date": date(2026, 5, 17),
        "match_time": time(19, 0),
        "stadium": "Bunyodkor stadioni",
        "status": "played",
        "home_score": 2,
        "away_score": 1,
        "attendance": 18500,
        "referee": "Ilgiz Tantashev",
        "possession_percent": 54,
        "shots": 13,
        "shots_on_target": 6,
        "corners": 5,
        "yellow_cards": 2,
        "red_cards": 0,
        "note": "Derbi o'yinida jamoa ikkinchi bo'limda ustunlikni saqlab qoldi.",
    },
    {
        "home_team": "Nasaf",
        "away_team": "Bunyodkor",
        "match_date": date(2026, 5, 21),
        "match_time": time(20, 0),
        "stadium": "Markaziy stadion, Qarshi",
        "status": "played",
        "home_score": 1,
        "away_score": 1,
        "attendance": 14200,
        "referee": "Rustam Lutfullin",
        "possession_percent": 49,
        "shots": 10,
        "shots_on_target": 4,
        "corners": 4,
        "yellow_cards": 3,
        "red_cards": 0,
        "note": "Safardagi muhim ochko.",
    },
    {
        "home_team": "Bunyodkor",
        "away_team": "Navbahor",
        "match_date": date(2026, 5, 25),
        "match_time": time(18, 30),
        "stadium": "Bunyodkor stadioni",
        "status": "upcoming",
        "attendance": 0,
        "referee": "Belgilanadi",
        "possession_percent": 50,
        "shots": 0,
        "shots_on_target": 0,
        "corners": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "note": "Uy uchrashuvi uchun tayyorgarlik davom etmoqda.",
    },
    {
        "home_team": "OKMK",
        "away_team": "Bunyodkor",
        "match_date": date(2026, 5, 30),
        "match_time": time(19, 30),
        "stadium": "OKMK sport majmuasi",
        "status": "upcoming",
        "attendance": 0,
        "referee": "Belgilanadi",
        "possession_percent": 50,
        "shots": 0,
        "shots_on_target": 0,
        "corners": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "note": "Safar o'yini.",
    },
    {
        "home_team": "Bunyodkor",
        "away_team": "Neftchi",
        "match_date": date(2026, 6, 4),
        "match_time": time(18, 0),
        "stadium": "Bunyodkor stadioni",
        "status": "upcoming",
        "attendance": 0,
        "referee": "Belgilanadi",
        "possession_percent": 50,
        "shots": 0,
        "shots_on_target": 0,
        "corners": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "note": "Keyingi tur uchrashuvi.",
    },
]


def seed_project_matches(apps, schema_editor):
    Match = apps.get_model("core", "Match")
    for item in MATCHES:
        lookup = {
            "home_team": item["home_team"],
            "away_team": item["away_team"],
            "match_date": item["match_date"],
            "match_time": item["match_time"],
        }
        Match.objects.update_or_create(defaults=item, **lookup)


def remove_project_matches(apps, schema_editor):
    Match = apps.get_model("core", "Match")
    for item in MATCHES:
        Match.objects.filter(
            home_team=item["home_team"],
            away_team=item["away_team"],
            match_date=item["match_date"],
            match_time=item["match_time"],
        ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0013_assign_player_photos"),
    ]

    operations = [
        migrations.RunPython(seed_project_matches, remove_project_matches),
    ]
