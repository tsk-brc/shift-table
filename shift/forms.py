from django import forms
from .models import Shift, ShiftType, Employee
from datetime import date


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ["employee", "date", "shift_type"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get("employee")
        date = cleaned_data.get("date")
        shift_type = cleaned_data.get("shift_type")

        if employee and date and shift_type:
            # 既存のシフトがあるかチェック
            existing_shift = Shift.objects.filter(employee=employee, date=date).exclude(
                pk=self.instance.pk if self.instance.pk else None
            )

            if existing_shift.exists():
                raise forms.ValidationError(
                    f"{employee.name}の{date}には既にシフトが登録されています。"
                )

            # 連続勤務日数制限をチェック
            if shift_type.is_work:
                # 一時的なシフトオブジェクトを作成してチェック
                temp_shift = Shift(employee=employee, date=date, shift_type=shift_type)
                warning = temp_shift.check_consecutive_work_days()
                if warning:
                    # 警告をフォームに追加（登録は可能）
                    self.add_warning("shift_type", warning["message"])

        return cleaned_data

    def add_warning(self, field, message):
        """警告メッセージを追加（エラーではない）"""
        if not hasattr(self, "_warnings"):
            self._warnings = {}
        if field not in self._warnings:
            self._warnings[field] = []
        self._warnings[field].append(message)

    def get_warnings(self):
        """警告メッセージを取得"""
        return getattr(self, "_warnings", {})

class AutoShiftForm(forms.Form):
    CREATION_MODE_CHOICES = [
        ('overwrite', '既存のシフトを上書きして1から作成'),
        ('fill_gaps', '既存のシフトを保持して空欄の日付に登録'),
    ]
    
    year = forms.IntegerField(
        label='年',
        min_value=1900,
        max_value=2099,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    month = forms.IntegerField(
        label='月',
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    creation_mode = forms.ChoiceField(
        label='作成モード',
        choices=CREATION_MODE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-control'}),
        initial='fill_gaps'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # デフォルト値を現在の年月に設定
        today = date.today()
        if not self.initial:
            self.initial = {
                'year': today.year,
                'month': today.month,
            }
