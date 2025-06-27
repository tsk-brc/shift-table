from django.shortcuts import render
from django.utils import timezone
from calendar import monthrange
from datetime import date, timedelta
from .models import Employee, Shift, ShiftType

# Create your views here.

def shift_table(request):
    # 年月の取得（クエリパラメータ or 今日）
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    num_days = monthrange(year, month)[1]
    days = [date(year, month, d) for d in range(1, num_days+1)]

    # 年月の範囲
    MIN_YEAR, MAX_YEAR = 1900, 2099
    # 前月・翌月の計算
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    # 前月・翌月が範囲内か
    show_prev = (prev_year > MIN_YEAR) or (prev_year == MIN_YEAR and prev_month >= 1)
    show_next = (next_year < MAX_YEAR) or (next_year == MAX_YEAR and next_month <= 12)

    employees = Employee.objects.all()
    shifts = Shift.objects.filter(date__year=year, date__month=month)
    shift_dict = {f"{s.employee_id}_{s.date.isoformat()}": s for s in shifts}
    shift_types = {st.id: st.name for st in ShiftType.objects.all()}

    # 各従業員×日付のシフト情報を事前に整理
    employee_shifts = {}
    for emp in employees:
        employee_shifts[emp.id] = {}
        for d in days:
            key = f"{emp.id}_{d.isoformat()}"
            employee_shifts[emp.id][d] = shift_dict.get(key)

    context = {
        'year': year,
        'month': month,
        'days': days,
        'employees': employees,
        'shift_dict': shift_dict,
        'shift_types': shift_types,
        'employee_shifts': employee_shifts,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'show_prev': show_prev,
        'show_next': show_next,
        'min_year': MIN_YEAR,
        'max_year': MAX_YEAR,
    }
    return render(request, 'shift/shift_table.html', context)
