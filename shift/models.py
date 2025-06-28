from django.db import models
from datetime import datetime, timedelta, date
from calendar import monthrange
import random

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

    @classmethod
    def create_auto_shifts(cls, year, month, creation_mode='fill_gaps'):
        """自動シフト作成"""
        settings = LaborLawSettings.get_current_settings()
        employees = list(Employee.objects.all())
        work_shift_types = list(ShiftType.objects.filter(is_work=True))
        rest_shift_type = ShiftType.objects.filter(is_work=False).first()
        
        if not employees:
            return {'success': False, 'error': '従業員が登録されていません。'}
        if not work_shift_types:
            return {'success': False, 'error': '勤務シフト種別が登録されていません。'}
        if not rest_shift_type:
            return {'success': False, 'error': '休みシフト種別が登録されていません。'}
        
        # 対象月の日数を取得
        num_days = monthrange(year, month)[1]
        target_dates = [date(year, month, d) for d in range(1, num_days + 1)]
        
        # 会社休日を取得
        company_holidays = set(CompanyHoliday.objects.filter(
            date__year=year, 
            date__month=month
        ).values_list('date', flat=True))
        
        # 既存シフトを取得
        existing_shifts = {}
        if creation_mode == 'fill_gaps':
            existing_shifts = {
                f"{s.employee_id}_{s.date.isoformat()}": s 
                for s in cls.objects.filter(date__year=year, date__month=month)
            }
        
        created_count = 0
        updated_count = 0
        
        # 各日付について処理
        for target_date in target_dates:
            shift_key = f"{target_date.isoformat()}"
            
            # 会社休日の場合は全員休み
            if target_date in company_holidays:
                for employee in employees:
                    employee_shift_key = f"{employee.id}_{shift_key}"
                    if creation_mode == 'fill_gaps' and employee_shift_key in existing_shifts:
                        continue
                    
                    shift, created = cls.objects.update_or_create(
                        employee=employee,
                        date=target_date,
                        defaults={'shift_type': rest_shift_type}
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                continue
            
            # その他の日は最低労働者数を満たすように調整
            available_employees = []
            for employee in employees:
                employee_shift_key = f"{employee.id}_{shift_key}"
                if creation_mode == 'fill_gaps' and employee_shift_key in existing_shifts:
                    continue
                available_employees.append(employee)
            
            if not available_employees:
                continue
            
            # 最低労働者数を満たすために必要な勤務者数
            current_workers = cls.objects.filter(
                date=target_date,
                shift_type__is_work=True
            ).exclude(employee__in=available_employees).count()
            
            needed_workers = max(0, settings.min_workers - current_workers)
            
            # 勤務者をランダムに選択
            work_employees = random.sample(available_employees, min(needed_workers, len(available_employees)))
            rest_employees = [emp for emp in available_employees if emp not in work_employees]
            
            # 勤務者にシフトを割り当て
            for employee in work_employees:
                # 連続勤務日数をチェック
                temp_shift = cls(
                    employee=employee,
                    date=target_date,
                    shift_type=work_shift_types[0]  # 仮の勤務シフト
                )
                consecutive_warning = temp_shift.check_consecutive_work_days()
                
                if consecutive_warning:
                    # 連続勤務日数制限に引っかかる場合は休みに
                    shift_type = rest_shift_type
                else:
                    shift_type = random.choice(work_shift_types)
                
                shift, created = cls.objects.update_or_create(
                    employee=employee,
                    date=target_date,
                    defaults={'shift_type': shift_type}
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            # 残りの従業員にランダムにシフトを割り当て
            for employee in rest_employees:
                # 連続勤務日数をチェック
                temp_shift = cls(
                    employee=employee,
                    date=target_date,
                    shift_type=work_shift_types[0]  # 仮の勤務シフト
                )
                consecutive_warning = temp_shift.check_consecutive_work_days()
                
                if consecutive_warning:
                    shift_type = rest_shift_type
                else:
                    # ランダムに勤務または休みを選択
                    shift_type = random.choice(work_shift_types + [rest_shift_type])
                
                shift, created = cls.objects.update_or_create(
                    employee=employee,
                    date=target_date,
                    defaults={'shift_type': shift_type}
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
        
        return {
            'success': True,
            'created_count': created_count,
            'updated_count': updated_count,
            'message': f'{created_count}件のシフトを作成し、{updated_count}件を更新しました。'
        }
