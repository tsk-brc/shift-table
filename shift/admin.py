from django.contrib import admin
from .models import Employee, ShiftType, Shift
from django.urls import reverse
from django.utils.html import format_html

admin.site.register(Employee)
admin.site.register(ShiftType)
admin.site.register(Shift)

# 管理画面の上部に「シフト表」リンクを追加
admin.site.site_header = 'シフト管理'
admin.site.site_title = 'シフト管理'
admin.site.index_title = format_html('<a href="{}" target="_blank">シフト表を見る</a>', reverse('shift_table'))
