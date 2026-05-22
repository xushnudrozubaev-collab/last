from django.db import migrations, models


def set_bunyodkor_club(apps, schema_editor):
    CoachProfile = apps.get_model("core", "CoachProfile")
    CoachProfile.objects.all().update(club_name="Bunyodkor")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_simplify_attendance_statuses"),
    ]

    operations = [
        migrations.AlterField(
            model_name="coachprofile",
            name="club_name",
            field=models.CharField(default="Bunyodkor", max_length=150),
        ),
        migrations.RunPython(set_bunyodkor_club, migrations.RunPython.noop),
    ]
