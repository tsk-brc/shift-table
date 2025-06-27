from django import forms
from .models import Shift, ShiftType, Employee

class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['employee', 'date', 'shift_type']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        date = cleaned_data.get('date')
        shift_type = cleaned_data.get('shift_type')
        
        if employee and date and shift_type:
            # 既存のシフトがあるかチェック
            existing_shift = Shift.objects.filter(
                employee=employee,
                date=date
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if existing_shift.exists():
                raise forms.ValidationError(
                    f'{employee.name}の{date}には既にシフトが登録されています。'
                )
            
            # 連続勤務日数制限をチェック
            if shift_type.is_work:
                # 一時的なシフトオブジェクトを作成してチェック
                temp_shift = Shift(
                    employee=employee,
                    date=date,
                    shift_type=shift_type
                )
                warning = temp_shift.check_consecutive_work_days()
                if warning:
                    # 警告をフォームに追加（登録は可能）
                    self.add_warning('shift_type', warning['message'])
        
        return cleaned_data

    def add_warning(self, field, message):
        """警告メッセージを追加（エラーではない）"""
        if not hasattr(self, '_warnings'):
            self._warnings = {}
        if field not in self._warnings:
            self._warnings[field] = []
        self._warnings[field].append(message)

    def get_warnings(self):
        """警告メッセージを取得"""
        return getattr(self, '_warnings', {}) 