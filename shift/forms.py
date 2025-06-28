from django import forms
from .models import Shift, ShiftType, Employee, CompanyHoliday
from datetime import date

COLOR_CHOICES = [
    ("#dc3545", "赤"),
    ("#007bff", "青"),
    ("#28a745", "緑"),
    ("#ffc107", "黄"),
    ("#fd7e14", "オレンジ"),
    ("#6f42c1", "紫"),
    ("#e83e8c", "ピンク"),
    ("#17a2b8", "水色"),
    ("#6c757d", "グレー"),
    ("#343a40", "黒"),
]

class ColorSelectWidget(forms.Widget):
    template_name = 'admin/widgets/color_select.html'

    def __init__(self, attrs=None):
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['value'] = value
        context['widget']['name'] = name
        context['widget']['color_choices'] = COLOR_CHOICES
        context['widget']['preset_codes'] = [c[0] for c in COLOR_CHOICES]
        return context

    class Media:
        css = {'all': ('admin/css/forms.css',)}
        js = ()

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
                
                # シフト種別ごとの人数制限をチェック
                worker_limit_warning = temp_shift.check_shift_type_worker_limits()
                if worker_limit_warning:
                    # 警告をフォームに追加（登録は可能）
                    self.add_warning("shift_type", worker_limit_warning["message"])

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

# class ShiftTypeForm(forms.ModelForm):
#     color = forms.CharField(
#         label='色',
#         widget=ColorSelectWidget,
#         required=True
#     )
#     
#     class Meta:
#         model = ShiftType
#         fields = ['name', 'is_work', 'color', 'min_workers', 'max_workers']  # role_min_workersを除外
#     
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # 役割一覧を取得
#         try:
#             from .models import Role
#             roles = Role.objects.all().order_by('name')
#             if roles.exists():
#                 # 役割ごとのフィールドを動的に追加
#                 for role in roles:
#                     field_name = f'role_min_workers_{role.id}'
#                     self.fields[field_name] = forms.IntegerField(
#                         label=f'{role.name}の最低人数',
#                         min_value=0,
#                         required=False,
#                         initial=0,
#                         help_text=f'{role.name}役割の最低必要人数を入力してください'
#                     )
#                 
#                 # 既存データがある場合は初期値を設定
#                 if self.instance and self.instance.pk:
#                     for role in roles:
#                         field_name = f'role_min_workers_{role.id}'
#                         if field_name in self.fields:
#                             min_worker_obj = self.instance.role_min_workers.filter(role=role).first()
#                             self.fields[field_name].initial = min_worker_obj.min_workers if min_worker_obj else 0
#         except:
#             # マイグレーション前などでRoleモデルが存在しない場合
#             pass
#     
#     def clean(self):
#         """個別フィールドをJSONに変換"""
#         cleaned_data = super().clean()
#         
#         # 役割別最低人数をJSONに変換
#         role_min_workers = {}
#         try:
#             from .models import Role
#             roles = Role.objects.all()
#             for role in roles:
#                 field_name = f'role_min_workers_{role.id}'
#                 if field_name in cleaned_data:
#                     value = cleaned_data.get(field_name)
#                     if value and value > 0:
#                         role_min_workers[role.name] = value
#         except:
#             pass
#         
#         cleaned_data['role_min_workers'] = role_min_workers
#         return cleaned_data
#     
#     def save(self, commit=True):
#         """フォームデータを保存"""
#         instance = super().save(commit=False)
#         
#         # 役割別最低人数を設定
#         if 'role_min_workers' in self.cleaned_data:
#             instance.role_min_workers = self.cleaned_data['role_min_workers']
#         
#         if commit:
#             instance.save()
#         return instance

class CompanyHolidayBulkAddForm(forms.Form):
    HOLIDAY_TYPE_CHOICES = [
        ('holidays', '祝日'),
        ('custom_weekday', '指定曜日'),
        ('date_range', '期間'),
    ]
    holiday_type = forms.ChoiceField(
        label='休日タイプ',
        choices=HOLIDAY_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        label='開始日',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    end_date = forms.DateField(
        label='終了日',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    weekday = forms.ChoiceField(
        label='曜日',
        choices=[
            (0, '月曜日'), (1, '火曜日'), (2, '水曜日'), (3, '木曜日'), (4, '金曜日'), (5, '土曜日'), (6, '日曜日'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    name = forms.CharField(
        label='休日名',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
