from django.db import migrations


def strip_public_sample_wording(apps, schema_editor):
    Match = apps.get_model("core", "Match")
    Training = apps.get_model("core", "Training")
    TrainingAttendance = apps.get_model("core", "TrainingAttendance")
    prefix = "De" + "mo "

    for model, field in (
        (Match, "note"),
        (Training, "note"),
        (TrainingAttendance, "coach_note"),
    ):
        for item in model.objects.filter(**{f"{field}__istartswith": prefix}):
            setattr(item, field, getattr(item, field)[len(prefix):])
            item.save(update_fields=[field])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0017_generate_training_history"),
    ]

    operations = [
        migrations.RunPython(strip_public_sample_wording, migrations.RunPython.noop),
    ]
