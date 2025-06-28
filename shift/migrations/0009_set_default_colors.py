# Generated manually

from django.db import migrations


def set_default_colors(apps, schema_editor):
    ShiftType = apps.get_model('shift', 'ShiftType')
    
    # 既存のシフト種別にデフォルトの色を設定
    default_colors = {
        '勤務': '#79aec8',  # 青
        '休み': '#dc3545',  # 赤
        '早番': '#28a745',  # 緑
        '遅番': '#ffc107',  # 黄
        '夜勤': '#6f42c1',  # 紫
    }
    
    for shift_type in ShiftType.objects.all():
        if shift_type.name in default_colors:
            shift_type.color = default_colors[shift_type.name]
        else:
            # 勤務日かどうかで色を分ける
            if shift_type.is_work:
                shift_type.color = '#79aec8'  # 青（勤務）
            else:
                shift_type.color = '#dc3545'  # 赤（休み）
        shift_type.save()


def reverse_default_colors(apps, schema_editor):
    # 逆操作は不要
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shift', '0008_add_color_to_shifttype'),
    ]

    operations = [
        migrations.RunPython(set_default_colors, reverse_default_colors),
    ] 