from django.contrib import admin
from django.contrib import messages
from .models import Employee, ShiftType, Shift, CompanyHoliday, LaborLawSettings
from .forms import ShiftForm
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import render
from django import forms
from datetime import date, timedelta
import jpholiday
from calendar import monthrange


class BulkHolidayForm(forms.Form):
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
            (0, '月曜日'),
            (1, '火曜日'),
            (2, '水曜日'),
            (3, '木曜日'),
            (4, '金曜日'),
            (5, '土曜日'),
            (6, '日曜日'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    holiday_name = forms.CharField(
        label='休日名',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )


@admin.register(CompanyHoliday)
class CompanyHolidayAdmin(admin.ModelAdmin):
    list_display = ['date', 'name', 'description']
    list_filter = ['date']
    search_fields = ['name', 'description']
    date_hierarchy = 'date'
    ordering = ['date']
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_bulk_add_button'] = True
        return super().changelist_view(request, extra_context)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-add/', self.admin_site.admin_view(self.bulk_add_view), name='shift_companyholiday_bulk_add'),
        ]
        return custom_urls + urls
    
    def bulk_add_view(self, request):
        if request.method == 'POST':
            form = BulkHolidayForm(request.POST)
            if form.is_valid():
                holiday_type = form.cleaned_data['holiday_type']
                start_date = form.cleaned_data['start_date']
                end_date = form.cleaned_data['end_date']
                weekday = form.cleaned_data['weekday']
                holiday_name = form.cleaned_data['holiday_name']
                
                # バリデーション
                if holiday_type in ['holidays', 'custom_weekday', 'date_range']:
                    if not start_date or not end_date:
                        messages.error(request, '開始日と終了日を指定してください。')
                        context = {
                            'title': '会社休日一括登録',
                            'form': form,
                            'opts': self.model._meta,
                        }
                        return render(request, 'admin/shift/companyholiday/bulk_add.html', context)
                
                if holiday_type == 'custom_weekday' and weekday is None:
                    messages.error(request, '曜日を選択してください。')
                    context = {
                        'title': '会社休日一括登録',
                        'form': form,
                        'opts': self.model._meta,
                    }
                    return render(request, 'admin/shift/companyholiday/bulk_add.html', context)
                
                created_count = 0
                skipped_count = 0
                
                if holiday_type == 'date_range' and start_date and end_date:
                    # 期間指定
                    current_date = start_date
                    while current_date <= end_date:
                        if not CompanyHoliday.objects.filter(date=current_date).exists():
                            CompanyHoliday.objects.create(
                                date=current_date,
                                name=holiday_name or f'休日 ({current_date})',
                                description=f'期間指定による一括登録'
                            )
                            created_count += 1
                        else:
                            skipped_count += 1
                        current_date += timedelta(days=1)
                
                elif holiday_type == 'custom_weekday' and start_date and end_date and weekday is not None:
                    # 指定曜日
                    current_date = start_date
                    while current_date <= end_date:
                        if current_date.weekday() == int(weekday):
                            if not CompanyHoliday.objects.filter(date=current_date).exists():
                                CompanyHoliday.objects.create(
                                    date=current_date,
                                    name=holiday_name or f'定休日 ({current_date.strftime("%A")})',
                                    description=f'指定曜日による一括登録'
                                )
                                created_count += 1
                            else:
                                skipped_count += 1
                        current_date += timedelta(days=1)
                
                elif holiday_type == 'holidays':
                    # 祝日
                    if not start_date or not end_date:
                        messages.error(request, '祝日を登録する場合は開始日と終了日を指定してください。')
                        form = BulkHolidayForm(request.POST)
                        context = {
                            'title': '会社休日一括登録',
                            'form': form,
                            'opts': self.model._meta,
                        }
                        return render(request, 'admin/shift/companyholiday/bulk_add.html', context)
                    
                    current_date = start_date
                    while current_date <= end_date:
                        if jpholiday.is_holiday(current_date):
                            if not CompanyHoliday.objects.filter(date=current_date).exists():
                                CompanyHoliday.objects.create(
                                    date=current_date,
                                    name=holiday_name or f'祝日 ({current_date})',
                                    description=f'祝日による一括登録'
                                )
                                created_count += 1
                            else:
                                skipped_count += 1
                        current_date += timedelta(days=1)
                
                messages.success(
                    request,
                    f'{created_count}件の会社休日を登録しました。{skipped_count}件は既に登録済みでした。'
                )
                return HttpResponseRedirect('../')
        else:
            form = BulkHolidayForm()
        
        context = {
            'title': '会社休日一括登録',
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/shift/companyholiday/bulk_add.html', context)


@admin.register(ShiftType)
class ShiftTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "is_work"]
    list_filter = ["is_work"]
    search_fields = ["name"]


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    form = ShiftForm
    list_display = ["employee", "date", "shift_type"]
    list_filter = ["employee", "shift_type", "date"]
    search_fields = ["employee__name", "shift_type__name"]
    date_hierarchy = "date"

    def save_model(self, request, obj, form, change):
        # フォームの警告をチェック
        warnings = form.get_warnings()
        if warnings:
            for field, messages_list in warnings.items():
                for message in messages_list:
                    messages.warning(request, f"警告: {message}")

        super().save_model(request, obj, form, change)


@admin.register(LaborLawSettings)
class LaborLawSettingsAdmin(admin.ModelAdmin):
    list_display = ['max_consecutive_work_days', 'min_workers', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # 設定は1つだけ作成可能
        return not LaborLawSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # 削除を許可
        return True
    
    def response_add(self, request, obj, post_url_continue=None):
        # 追加後は変更画面にリダイレクト（「保存してもう1つ追加」ボタンを非表示にするため）
        return self.response_post_save_add(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        # 作成日時と更新日時のみ読み取り専用
        return ['created_at', 'updated_at']
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        # 追加画面で「保存してもう一つ追加」ボタンを非表示にする
        extra_context = extra_context or {}
        if object_id is None:  # 追加画面の場合
            extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


admin.site.register(Employee)

# 管理画面の上部に「シフト表」リンクを追加
admin.site.site_header = 'シフト管理'
admin.site.site_title = 'シフト管理'
admin.site.index_title = format_html('<a href="{}" target="_blank">シフト表を見る</a>', reverse('shift_table'))
