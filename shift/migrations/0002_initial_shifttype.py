from django.db import migrations


def create_initial_shifttypes(apps, schema_editor):
    ShiftType = apps.get_model("shift", "ShiftType")
    ShiftType.objects.get_or_create(name="出勤")
    ShiftType.objects.get_or_create(name="休み")


class Migration(migrations.Migration):
    dependencies = [
        ("shift", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(create_initial_shifttypes),
    ]
