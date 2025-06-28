# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shift', '0007_alter_shift_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='shifttype',
            name='color',
            field=models.CharField(
                default='#79aec8',
                help_text='シフト表での表示色（例: #79aec8）',
                max_length=7,
                verbose_name='色'
            ),
        ),
    ] 