from django.db import models
from datetime import datetime, timedelta

# Create your models here.

class Employee(models.Model):
    name = models.CharField('氏名', max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '従業員'
        verbose_name_plural = '従業員'

class ShiftType(models.Model):
    name = models.CharField('シフト種別名', max_length=50, unique=True)
    is_work = models.BooleanField('勤務日', default=True, help_text='休み以外の勤務日かどうか')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'シフト種別'
        verbose_name_plural = 'シフト種別'

class CompanyHoliday(models.Model):
    date = models.DateField('日付', unique=True)
    name = models.CharField('休日名', max_length=100)
    description = models.TextField('説明', blank=True)

    def __str__(self):
        return f"{self.date} {self.name}"

    class Meta:
        verbose_name = '会社休日'
        verbose_name_plural = '会社休日'
        ordering = ['date']

class LaborLawSettings(models.Model):
    max_consecutive_work_days = models.PositiveIntegerField(
        '最大連続勤務日数', 
        default=6,
        help_text='連続勤務日数の上限'
    )
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    def __str__(self):
        return f"最大連続勤務日数: {self.max_consecutive_work_days}日"

    class Meta:
        verbose_name = '労働設定'
        verbose_name_plural = '労働設定'

    @classmethod
    def get_current_settings(cls):
        """現在の設定を取得（設定がない場合はデフォルト値で作成）"""
        settings, created = cls.objects.get_or_create(
            defaults={'max_consecutive_work_days': 6}
        )
        return settings

class Shift(models.Model):
    employee = models.ForeignKey(Employee, verbose_name='従業員', on_delete=models.CASCADE)
    date = models.DateField('日付')
    shift_type = models.ForeignKey(ShiftType, verbose_name='シフト種別', on_delete=models.PROTECT)

    class Meta:
        unique_together = ('employee', 'date')
        verbose_name = 'シフト'
        verbose_name_plural = 'シフト'

    def __str__(self):
        return f"{self.date} {self.employee.name} {self.shift_type.name}"

    def check_consecutive_work_days(self):
        """連続勤務日数制限をチェック"""
        if not self.shift_type.is_work:
            return None  # 休みの場合はチェック不要
        
        settings = LaborLawSettings.get_current_settings()
        max_days = settings.max_consecutive_work_days
        
        # 指定日から前後7日間のシフトを取得
        start_date = self.date - timedelta(days=7)
        end_date = self.date + timedelta(days=7)
        
        shifts = Shift.objects.filter(
            employee=self.employee,
            date__range=[start_date, end_date],
            shift_type__is_work=True
        ).order_by('date')
        
        # 連続勤務日数を計算
        consecutive_days = 0
        current_date = None
        
        for shift in shifts:
            if current_date is None:
                consecutive_days = 1
                current_date = shift.date
            elif (shift.date - current_date).days == 1:
                consecutive_days += 1
                current_date = shift.date
            else:
                consecutive_days = 1
                current_date = shift.date
        
        if consecutive_days > max_days:
            return {
                'warning': True,
                'message': f'連続勤務日数が{consecutive_days}日となり、設定された上限({max_days}日)を超えています。',
                'consecutive_days': consecutive_days,
                'max_days': max_days
            }
        
        return None
