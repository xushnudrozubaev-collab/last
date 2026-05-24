from datetime import date, timedelta, time

from django.db import migrations


OPPONENTS = [
    "Paxtakor",
    "Nasaf",
    "Navbahor",
    "OKMK",
    "Neftchi",
    "Surxon",
    "Sog'diyona",
    "Qizilqum",
    "Andijon",
    "Dinamo",
    "Metallurg",
    "Lokomotiv",
    "Mash'al",
    "Qo'qon-1912",
]

STADIUMS = {
    "Bunyodkor": "Bunyodkor stadioni",
    "Paxtakor": "Paxtakor markaziy stadioni",
    "Nasaf": "Markaziy stadion, Qarshi",
    "Navbahor": "Markaziy stadion, Namangan",
    "OKMK": "OKMK sport majmuasi",
    "Neftchi": "Istiqlol stadioni",
    "Surxon": "Surxon arena",
    "Sog'diyona": "So'g'diyona sport majmuasi",
    "Qizilqum": "Yoshlik sport majmuasi",
    "Andijon": "Bobur arena",
    "Dinamo": "Dinamo stadioni",
    "Metallurg": "Metallurg stadioni",
    "Lokomotiv": "Lokomotiv stadioni",
    "Mash'al": "Bahrom Vafoev stadioni",
    "Qo'qon-1912": "Qo'qon markaziy stadioni",
}

REFEREES = [
    "Ilgiz Tantashev",
    "Rustam Lutfullin",
    "Firdavs Norsafarov",
    "Akobirxo'ja Shukurullayev",
    "Sherzod Qosimov",
    "Dilmurod Sodiqov",
    "Jasur Muxtorov",
    "Aziz Asimov",
]


def build_match(index):
    match_date = date(2026, 5, 25) - timedelta(days=index)
    opponent = OPPONENTS[index % len(OPPONENTS)]
    home_is_project = index % 2 == 0
    base_score = index % 6
    if base_score in {0, 3}:
        our_score, opponent_score = 2 + (index % 2), 0
    elif base_score in {1, 4}:
        our_score, opponent_score = 1 + (index % 2), 1 + (index % 2)
    else:
        our_score, opponent_score = 0, 1 + (index % 2)

    home_team = "Bunyodkor" if home_is_project else opponent
    away_team = opponent if home_is_project else "Bunyodkor"
    home_score = our_score if home_is_project else opponent_score
    away_score = opponent_score if home_is_project else our_score

    return {
        "home_team": home_team,
        "away_team": away_team,
        "match_date": match_date,
        "match_time": time(18 + (index % 3), 0 if index % 2 == 0 else 30),
        "stadium": STADIUMS[home_team],
        "status": "played",
        "home_score": home_score,
        "away_score": away_score,
        "attendance": 7200 + (index * 173) % 12800,
        "referee": REFEREES[index % len(REFEREES)],
        "possession_percent": 45 + (index * 7) % 16,
        "shots": 7 + (index * 3) % 11,
        "shots_on_target": 2 + (index * 2) % 7,
        "corners": 2 + (index * 5) % 7,
        "yellow_cards": 1 + index % 4,
        "red_cards": 1 if index % 31 == 0 else 0,
        "note": "Mavsum tarixi uchun avtomatik qo'shilgan yakunlangan o'yin.",
    }


def generate_match_history(apps, schema_editor):
    Match = apps.get_model("core", "Match")
    for index in range(100):
        item = build_match(index)
        lookup = {
            "home_team": item["home_team"],
            "away_team": item["away_team"],
            "match_date": item["match_date"],
            "match_time": item["match_time"],
        }
        Match.objects.update_or_create(defaults=item, **lookup)


def remove_match_history(apps, schema_editor):
    Match = apps.get_model("core", "Match")
    notes = "Mavsum tarixi uchun avtomatik qo'shilgan yakunlangan o'yin."
    Match.objects.filter(note=notes).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0015_expand_completed_matches"),
    ]

    operations = [
        migrations.RunPython(generate_match_history, remove_match_history),
    ]
