"""
Iyun 2026 uchun o'yin va mashg'ulot ma'lumotlari.
  - 12 ta yakunlangan o'yin (1-iyun ... 2-iyun chiqib qolmasin deb 1-25 iyun)
  - 20 ta mashg'ulot (1-25 iyun)
"""
from datetime import date, timedelta, time

from django.db import migrations


# ---------- O'yinlar uchun yordamchi ma'lumotlar ----------

OPPONENTS = [
    "Paxtakor", "Nasaf", "Navbahor", "OKMK", "Neftchi",
    "Surxon", "Sog'diyona", "Qizilqum", "Andijon", "Dinamo",
    "Metallurg", "Lokomotiv",
]

STADIUMS = {
    "Bunyodkor":  "Bunyodkor stadioni",
    "Paxtakor":   "Paxtakor markaziy stadioni",
    "Nasaf":      "Markaziy stadion, Qarshi",
    "Navbahor":   "Markaziy stadion, Namangan",
    "OKMK":       "OKMK sport majmuasi",
    "Neftchi":    "Istiqlol stadioni",
    "Surxon":     "Surxon arena",
    "Sog'diyona": "So'g'diyona sport majmuasi",
    "Qizilqum":   "Yoshlik sport majmuasi",
    "Andijon":    "Bobur arena",
    "Dinamo":     "Dinamo stadioni",
    "Metallurg":  "Metallurg stadioni",
    "Lokomotiv":  "Lokomotiv stadioni",
}

REFEREES = [
    "Ilgiz Tantashev", "Rustam Lutfullin", "Firdavs Norsafarov",
    "Akobirxo'ja Shukurullayev", "Sherzod Qosimov", "Dilmurod Sodiqov",
]

# 12 ta o'yin: 1-iyun, 4, 7, 9, 11, 13, 15, 17, 19, 21, 24, 26
MATCH_DAYS = [1, 4, 7, 9, 11, 13, 15, 17, 19, 21, 24, 26]


def _build_june_match(idx):
    """idx 0..11 — har biri MATCH_DAYS qatoridagi sana"""
    day = MATCH_DAYS[idx]
    match_date = date(2026, 6, day)
    opponent = OPPONENTS[idx % len(OPPONENTS)]
    home_is_project = idx % 2 == 0

    # Natija: 6 xil sxema (g'alaba/durang/mag'lubiyat aralash)
    pattern = idx % 6
    if pattern in (0, 3):        # g'alaba
        our, opp = 2 + idx % 2, 0
    elif pattern in (1, 4):      # durang
        our, opp = 1 + idx % 2, 1 + idx % 2
    else:                        # mag'lubiyat
        our, opp = 0, 1 + idx % 2

    home_team = "Bunyodkor" if home_is_project else opponent
    away_team = opponent if home_is_project else "Bunyodkor"
    home_score = our if home_is_project else opp
    away_score = opp if home_is_project else our

    return {
        "home_team":          home_team,
        "away_team":          away_team,
        "match_date":         match_date,
        "match_time":         time(17 + idx % 3, 0 if idx % 2 == 0 else 30),
        "stadium":            STADIUMS.get(home_team, "Bunyodkor stadioni"),
        "status":             "played",
        "home_score":         home_score,
        "away_score":         away_score,
        "attendance":         8000 + (idx * 213) % 14000,
        "referee":            REFEREES[idx % len(REFEREES)],
        "possession_percent": 47 + (idx * 5) % 14,
        "shots":              8 + (idx * 3) % 10,
        "shots_on_target":    3 + (idx * 2) % 6,
        "corners":            3 + (idx * 4) % 6,
        "yellow_cards":       1 + idx % 3,
        "red_cards":          1 if idx % 11 == 0 else 0,
        "note":               "Iyun 2026 uchun avtomatik qo'shilgan o'yin.",
    }


# ---------- Mashg'ulotlar uchun yordamchi ma'lumotlar ----------

TRAINING_TYPES  = ["tactics", "fitness", "technical", "recovery"]
TRAINING_TITLES = [
    "Pressing va himoya bloki",
    "Tezkor hujumlar",
    "Standart vaziyatlars",
    "Tiklanish va monitoring",
    "Yakuniy paslar",
    "Jismoniy yuklama",
    "Kombinatsion o'yin",
    "Himoyani kuchaytirish",
    "Set-pis mashqlari",
    "Yuklama va kuch",
]

STATUS_PRESENT  = "Qatnashdi"
STATUS_ABSENT   = "Qatnashmadi"
INJURY_NO       = "Yo'q"
PHYSICAL_GOOD   = "good"
PHYSICAL_TIRED  = "tired"
ACTIVITY_MEDIUM = "medium"
ACTIVITY_HIGH   = "high"
DISCIPLINE_GOOD = "good"

# 20 ta mashg'ulot: 1-iyundan 25-iyungacha (har kuni emas, dam olish kunlari yo'q)
TRAINING_DAYS = [1, 2, 3, 5, 6, 8, 10, 12, 14, 16, 17, 18, 20, 22, 23, 24, 25, 26, 27, 28]


def generate_june_data(apps, schema_editor):
    Match    = apps.get_model("core", "Match")
    Training = apps.get_model("core", "Training")
    TrainingAttendance = apps.get_model("core", "TrainingAttendance")
    Player   = apps.get_model("core", "Player")

    # --- O'yinlar ---
    for idx in range(len(MATCH_DAYS)):
        item   = _build_june_match(idx)
        lookup = {
            "home_team":  item["home_team"],
            "away_team":  item["away_team"],
            "match_date": item["match_date"],
        }
        Match.objects.update_or_create(defaults=item, **lookup)

    # --- Mashg'ulotlar ---
    players = list(Player.objects.order_by("shirt_number", "full_name"))
    if not players:
        return

    for idx, day in enumerate(TRAINING_DAYS):
        training_date = date(2026, 6, day)
        start_hour    = 9 + (idx % 3)
        duration      = 75 + (idx % 4) * 15
        start_time    = time(start_hour, 0)
        end_time      = time(start_hour + duration // 60, duration % 60)
        title         = f"{TRAINING_TITLES[idx % len(TRAINING_TITLES)]} (Iyun #{idx + 1})"

        training, _ = Training.objects.update_or_create(
            title=title,
            training_date=training_date,
            defaults={
                "training_type":      TRAINING_TYPES[idx % len(TRAINING_TYPES)],
                "start_time":         start_time,
                "end_time":           end_time,
                "location":           "Bunyodkor akademiyasi",
                "note":               "Iyun 2026 uchun avtomatik mashg'ulot.",
                "attendance_total":   len(players),
                "attendance_present": 0,
            },
        )

        present_count = 0
        for pi, player in enumerate(players):
            absent  = (pi + idx) % 11 == 0
            status  = STATUS_ABSENT if absent else STATUS_PRESENT
            if not absent:
                present_count += 1
            rating         = 6 + ((pi + idx) % 5)
            activity_score = 5 + ((pi * 2 + idx) % 6)

            TrainingAttendance.objects.update_or_create(
                training=training,
                player=player,
                defaults={
                    "attendance_status":       status,
                    "physical_condition":      PHYSICAL_TIRED if idx % 9 == 0 else PHYSICAL_GOOD,
                    "activity_level":          ACTIVITY_HIGH if activity_score >= 8 else ACTIVITY_MEDIUM,
                    "discipline":              DISCIPLINE_GOOD,
                    "rating":                  rating,
                    "attended_minutes":        0 if absent else duration,
                    "training_duration_minutes": duration,
                    "fatigue_level":           2 + (idx + pi) % 5,
                    "pain_level":              1 + (idx + pi) % 3,
                    "sleep_quality":           6 + (pi + idx) % 4,
                    "activity_score":          1 if absent else activity_score,
                    "injury_status":           INJURY_NO,
                    "coach_note":              "Iyun mashg'ulot yozuvi.",
                },
            )

        training.attendance_present = present_count
        training.save(update_fields=["attendance_present", "attendance_total"])


def remove_june_data(apps, schema_editor):
    Match    = apps.get_model("core", "Match")
    Training = apps.get_model("core", "Training")
    Match.objects.filter(note="Iyun 2026 uchun avtomatik qo'shilgan o'yin.").delete()
    Training.objects.filter(note="Iyun 2026 uchun avtomatik mashg'ulot.").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0019_add_ai_assistant_models"),
    ]

    operations = [
        migrations.RunPython(generate_june_data, remove_june_data),
    ]
