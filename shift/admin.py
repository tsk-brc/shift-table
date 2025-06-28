from django.contrib import admin
from django.contrib import messages
from .models import Employee, ShiftType, Shift, CompanyHoliday, LaborLawSettings
from .forms import ShiftForm
from django.urls import reverse
from django.utils.html import format_html


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
    list_display = ["max_consecutive_work_days", "updated_at"]
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


admin.site.register(Employee)
admin.site.register(CompanyHoliday)

# 管理画面の上部に「シフト表」リンクを追加
admin.site.site_header = "シフト管理"
admin.site.site_title = "シフト管理"
admin.site.index_title = format_html(
    '<a href="{}" target="_blank">シフト表を見る</a>', reverse("shift_table")
)
