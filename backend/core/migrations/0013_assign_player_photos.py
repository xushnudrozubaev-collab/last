from django.db import migrations


PLAYER_PHOTOS = {
    "O‘tkir Yusupov": "players/otkir-yusupov.jpg",
    "Abduqodir Husanov": "players/abduqodir-husanov.jpg",
    "Hojiakbar Alijonov": "players/hojiakbar-alijonov.jpg",
    "Sherzod Nasrullayev": "players/sherzod-nasrullayev.jpg",
    "Husniddin Aliqulov": "players/husniddin-aliqulov.jpg",
    "Akmal Mozgovoy": "players/akmal-mozgovoy.jpg",
    "Odiljon Hamrobekov": "players/odiljon-hamrobekov.jpg",
    "Eldor Shomurodov": "players/eldor-shomurodov.jpg",
    "Abbosbek Fayzullayev": "players/abbosbek-fayzullayev.jpg",
    "Jaloliddin Masharipov": "players/jaloliddin-masharipov.jpg",
    "Azizbek Turg‘unboyev": "players/azizbek-turgunboyev.jpg",
}


def assign_player_photos(apps, schema_editor):
    Player = apps.get_model("core", "Player")
    for full_name, photo in PLAYER_PHOTOS.items():
        Player.objects.filter(full_name=full_name).update(photo=photo)


def clear_player_photos(apps, schema_editor):
    Player = apps.get_model("core", "Player")
    Player.objects.filter(full_name__in=PLAYER_PHOTOS.keys()).update(photo="")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_bunyodkor_project_club"),
    ]

    operations = [
        migrations.RunPython(assign_player_photos, clear_player_photos),
    ]
