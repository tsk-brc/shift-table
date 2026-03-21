import re
from datetime import timedelta

from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .forms import AutoShiftForm, CompanyHolidayBulkAddForm, ShiftForm
from .models import (
    CompanyHoliday,
    Employee,
    LaborLawSettings,
    Role,
    Shift,
    ShiftType,
    ShiftTypeRoleMinWorker,
)

jpholiday = None
try:
    import jpholiday
except ImportError:
    jpholiday = None


@admin.register(CompanyHoliday)
class CompanyHolidayAdmin(admin.ModelAdmin):
    list_display = ["date", "name", "description"]
    list_filter = ["date"]
    search_fields = ["name", "description"]
    date_hierarchy = "date"
    ordering = ["date"]

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_bulk_add_button"] = True
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "bulk-add/",
                self.admin_site.admin_view(self.bulk_add_view),
                name="shift_companyholiday_bulk_add",
            ),
        ]
        return custom_urls + urls

    def bulk_add_view(self, request):
        """一括追加ビュー"""
        if request.method == "POST":
            form = CompanyHolidayBulkAddForm(request.POST)
            if form.is_valid():
                # フォーム処理（既存のコード）
                holiday_type = form.cleaned_data["holiday_type"]
                start_date = form.cleaned_data["start_date"]
                end_date = form.cleaned_data["end_date"]
                weekday = form.cleaned_data["weekday"]
                holiday_name = form.cleaned_data["name"]

                if holiday_type and start_date and end_date:
                    created_count = 0

                    if holiday_type == "custom_weekday":
                        if weekday is not None:
                            current = start_date
                            while current <= end_date:
                                if current.weekday() == weekday:
                                    holiday, created = (
                                        CompanyHoliday.objects.get_or_create(
                                            date=current,
                                            defaults={
                                                "name": holiday_name or "指定曜日休日",
                                                "description": "",
                                            },
                                        )
                                    )
                                    if created:
                                        created_count += 1
                                current += timedelta(days=1)

                    elif holiday_type == "holidays":
                        current = start_date
                        while current <= end_date:
                            # 祝日かどうかをチェック
                            if jpholiday and jpholiday.is_holiday(current):
                                holiday, created = CompanyHoliday.objects.get_or_create(
                                    date=current,
                                    defaults={
                                        "name": holiday_name or "祝日",
                                        "description": "",
                                    },
                                )
                                if created:
                                    created_count += 1
                            current += timedelta(days=1)

                    elif holiday_type == "date_range":
                        current = start_date
                        while current <= end_date:
                            holiday, created = CompanyHoliday.objects.get_or_create(
                                date=current,
                                defaults={
                                    "name": holiday_name or "期間休日",
                                    "description": "",
                                },
                            )
                            if created:
                                created_count += 1
                            current += timedelta(days=1)

                    if created_count > 0:
                        messages.success(
                            request, f"{created_count}件の会社休日を追加しました。"
                        )
                    else:
                        messages.warning(request, "追加された会社休日はありません。")

                    return redirect("admin:shift_companyholiday_changelist")
                else:
                    messages.error(request, "必要な情報を入力してください。")
        else:
            form = CompanyHolidayBulkAddForm()

        context = {
            "title": "会社休日一括追加",
            "opts": self.model._meta,
            "form": form,
        }
        return render(request, "admin/shift/companyholiday/bulk_add.html", context)


class ShiftTypeRoleMinWorkerInline(admin.TabularInline):
    model = ShiftTypeRoleMinWorker
    extra = 0
    verbose_name = "役割別最低人数"
    verbose_name_plural = "役割別最低人数"
    fields = ("role", "min_workers")
    verbose_name_display = {"role": "役割", "min_workers": "最低人数"}

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        form = formset.form
        form.base_fields["role"].label = "役割"
        form.base_fields["min_workers"].label = "最低人数"
        return formset


@admin.register(ShiftType)
class ShiftTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "is_work", "min_workers", "max_workers", "color_display"]
    list_filter = ["is_work"]
    search_fields = ["name"]
    inlines = [ShiftTypeRoleMinWorkerInline]

    def color_display(self, obj):
        if obj.color:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
                obj.color,
                obj.color,
            )
        return "-"

    color_display.short_description = "色"


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ["employee", "date", "shift_type"]
    list_filter = ["date", "shift_type", "employee"]
    search_fields = ["employee__name", "shift_type__name"]
    date_hierarchy = "date"
    form = ShiftForm

    def changelist_view(self, request, extra_context=None):
        """一覧画面に自動シフト作成リンクを追加"""
        extra_context = extra_context or {}
        extra_context["auto_create_url"] = "admin:shift_auto_create"
        extra_context["title"] = "シフト管理"
        extra_context["subtitle"] = None  # サブタイトルを削除

        # モデルのverbose_nameを一時的に変更
        original_verbose_name = self.model._meta.verbose_name
        original_verbose_name_plural = self.model._meta.verbose_name_plural
        self.model._meta.verbose_name = "シフト管理"
        self.model._meta.verbose_name_plural = "シフト管理"

        response = super().changelist_view(request, extra_context)

        # 元に戻す
        self.model._meta.verbose_name = original_verbose_name
        self.model._meta.verbose_name_plural = original_verbose_name_plural

        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "auto-create/",
                self.admin_site.admin_view(self.auto_create_view),
                name="shift_auto_create",
            ),
        ]
        return custom_urls + urls

    def auto_create_view(self, request):
        """自動シフト作成ビュー"""
        if request.method == "POST":
            form = AutoShiftForm(request.POST)
            if form.is_valid():
                year = form.cleaned_data["year"]
                month = form.cleaned_data["month"]
                creation_mode = form.cleaned_data["creation_mode"]

                # 自動シフト作成を実行
                result = Shift.create_auto_shifts(year, month, creation_mode)

                if result["success"]:
                    messages.success(request, result["message"])
                    return redirect("admin:shift_shift_changelist")
                else:
                    messages.error(request, result["error"])
        else:
            form = AutoShiftForm()

        context = {
            "title": "自動シフト作成",
            "form": form,
            "opts": self.model._meta,
            "site_title": "自動シフト作成",
            "site_header": "自動シフト作成",
            "subtitle": None,  # サブタイトルを削除
        }

        response = render(request, "admin/shift/auto_create.html", context)

        # レスポンスの内容を直接修正
        if hasattr(response, "content"):
            content = response.content.decode("utf-8")
            # h1タグの内容を修正
            content = re.sub(
                r"<h1[^>]*>.*?自動シフト作成.*?自動シフト作成.*?</h1>",
                "<h1>自動シフト作成</h1>",
                content,
                flags=re.DOTALL,
            )
            content = re.sub(
                r"<h1[^>]*>.*?自動シフト作成.*?</h1>",
                "<h1>自動シフト作成</h1>",
                content,
                flags=re.DOTALL,
            )
            # タイトルタグも修正
            content = re.sub(
                r"<title>.*?自動シフト作成.*?自動シフト作成.*?</title>",
                "<title>自動シフト作成</title>",
                content,
                flags=re.DOTALL,
            )
            response.content = content.encode("utf-8")

        return response


@admin.register(LaborLawSettings)
class LaborLawSettingsAdmin(admin.ModelAdmin):
    list_display = ["max_consecutive_work_days", "min_workers", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]

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
        return ["created_at", "updated_at"]

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        # 追加画面で「保存してもう一つ追加」ボタンを非表示にする
        extra_context = extra_context or {}
        if object_id is None:  # 追加画面の場合
            extra_context["show_save_and_add_another"] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name", "description"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["name", "get_roles"]
    search_fields = ["name"]
    filter_horizontal = ["roles"]

    def get_roles(self, obj):
        return ", ".join([role.name for role in obj.roles.all()])

    get_roles.short_description = "役割"


# 管理画面の上部に「シフト表」リンクを追加
admin.site.site_header = "シフト管理"
admin.site.site_title = "シフト管理"
admin.site.index_title = format_html(
    '<a href="{}" target="_blank">シフト表を見る</a>', reverse("shift_table")
)
