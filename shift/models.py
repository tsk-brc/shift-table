from django.db import models
from datetime import datetime, timedelta

# Create your models here.


class Employee(models.Model):
    name = models.CharField("氏名", max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "従業員"
        verbose_name_plural = "従業員"


class ShiftType(models.Model):
    name = models.CharField("シフト種別名", max_length=50, unique=True)
    is_work = models.BooleanField(
        "勤務日", default=True, help_text="休み以外の勤務日かどうか"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "シフト種別"
        verbose_name_plural = "シフト種別"


class CompanyHoliday(models.Model):
    date = models.DateField("日付", unique=True)
    name = models.CharField("休日名", max_length=100)
    description = models.TextField("説明", blank=True)

    def __str__(self):
        return f"{self.date} {self.name}"

    class Meta:
        verbose_name = "会社休日"
        verbose_name_plural = "会社休日"
        ordering = ["date"]


class LaborLawSettings(models.Model):
    max_consecutive_work_days = models.PositiveIntegerField(
        "最大連続勤務日数", default=6, help_text="連続勤務日数の上限"
    )
    min_workers = models.PositiveIntegerField(
        "最低労働者数", default=1, help_text="1日に必要な最低労働者数（休み以外）"
    )
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    def __str__(self):
        return f"最大連続勤務日数: {self.max_consecutive_work_days}日, 最低労働者数: {self.min_workers}人"

    class Meta:
        verbose_name = "労働設定"
        verbose_name_plural = "労働設定"

    @classmethod
    def get_current_settings(cls):
        """現在の設定を取得（設定がない場合はデフォルト値で作成）"""
        settings, created = cls.objects.get_or_create(
            defaults={
                "max_consecutive_work_days": 6,
                "min_workers": 1
            }
        )
        return settings


class Shift(models.Model):
    employee = models.ForeignKey(
        Employee, verbose_name="従業員", on_delete=models.CASCADE
    )
    date = models.DateField("日付")
    shift_type = models.ForeignKey(
        ShiftType, verbose_name="シフト種別", on_delete=models.PROTECT
    )

    class Meta:
        unique_together = ("employee", "date")
        verbose_name = "シフト"
        verbose_name_plural = "シフト"

    def __str__(self):
        return f"{self.date} {self.employee.name} {self.shift_type.name}"

    def check_consecutive_work_days(self):
        """連続勤務日数制限をチェック"""
        if not self.shift_type.is_work:
            return None  # 休みの場合はチェック不要
        
        settings = LaborLawSettings.get_current_settings()
        max_days = settings.max_consecutive_work_days
        
        # 指定日から前後「最大連続勤務日数」分のシフトを取得
        start_date = self.date - timedelta(days=max_days)
        end_date = self.date + timedelta(days=max_days)
        
        # 勤務日のみのシフトを取得（休みは除外）
        shifts = Shift.objects.filter(
            employee=self.employee,
            date__range=[start_date, end_date],
            shift_type__is_work=True
        ).exclude(id=self.id)  # 現在のシフトを除外（更新時）
        
        # 勤務日の日付リストを作成
        work_dates = set(shifts.values_list('date', flat=True))
        if self.shift_type.is_work:  # 現在のシフトが勤務日の場合のみ追加
            work_dates.add(self.date)
        
        # 連続勤務日数を計算（勤務日のみ）
        max_consecutive = 0
        current_consecutive = 0
        sorted_dates = sorted(work_dates)
        
        for i, work_date in enumerate(sorted_dates):
            if i == 0:
                current_consecutive = 1
            else:
                prev_date = sorted_dates[i-1]
                if (work_date - prev_date).days == 1:
                    current_consecutive += 1
                else:
                    current_consecutive = 1
            
            max_consecutive = max(max_consecutive, current_consecutive)
        
        if max_consecutive > max_days:
            return {
                'warning': True,
                'message': f'連続勤務日数が{max_consecutive}日となり、設定された上限({max_days}日)を超えています。',
                'consecutive_days': max_consecutive,
                'max_days': max_days
            }
        
        return None

    def check_min_workers(self):
        """最低労働者数制限をチェック"""
        # 会社休日の場合はチェックしない
        company_holiday = CompanyHoliday.objects.filter(date=self.date).first()
        if company_holiday:
            return None
        
        settings = LaborLawSettings.get_current_settings()
        min_workers = settings.min_workers
        
        # 指定日の勤務者数を取得
        work_shifts = Shift.objects.filter(
            date=self.date,
            shift_type__is_work=True
        ).exclude(id=self.id)  # 現在のシフトを除外（更新時）
        
        work_count = work_shifts.count()
        
        # 現在のシフトが勤務日の場合、カウントに追加
        if self.shift_type.is_work:
            work_count += 1
        
        if work_count < min_workers:
            return {
                'warning': True,
                'message': f'{self.date}の勤務者数が{work_count}人となり、設定された最低労働者数({min_workers}人)を下回っています。',
                'current_workers': work_count,
                'min_workers': min_workers
            }
        
        return None
