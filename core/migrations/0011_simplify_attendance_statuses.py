from django.db import migrations, models


def normalize_attendance_statuses(apps, schema_editor):
    TrainingAttendance = apps.get_model("core", "TrainingAttendance")
    TrainingAttendance.objects.filter(
        attendance_status__in=["Kelmadi", "Kechikdi", "Uzrli sabab"]
    ).update(attendance_status="Qatnashmadi")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0010_trainingattendance_blood_pressure_and_more"),
    ]

    operations = [
        migrations.RunPython(normalize_attendance_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="trainingattendance",
            name="attendance_status",
            field=models.CharField(
                choices=[
                    ("Qatnashdi", "Qatnashdi"),
                    ("Qatnashmadi", "Qatnashmadi"),
                ],
                default="Qatnashdi",
                max_length=20,
            ),
        ),
    ]
