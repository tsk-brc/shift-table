from django.shortcuts import render
from django.utils import timezone
from calendar import monthrange
from datetime import date, timedelta
from .models import Employee, Shift, ShiftType, CompanyHoliday
import jpholiday
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

# Create your views here.

def shift_table(request):
    # 年月の取得（クエリパラメータ or 今日）
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    num_days = monthrange(year, month)[1]
    days = [date(year, month, d) for d in range(1, num_days+1)]

    # 会社休日を取得
    company_holidays = CompanyHoliday.objects.filter(date__year=year, date__month=month)
    company_holiday_dates = {ch.date: ch.name for ch in company_holidays}

    # 各日付の曜日と祝日情報を取得
    day_info = {}
    for d in days:
        weekday = d.strftime('%a')  # Mon, Tue, Wed, etc.
        weekday_ja = {'Mon': '月', 'Tue': '火', 'Wed': '水', 'Thu': '木', 'Fri': '金', 'Sat': '土', 'Sun': '日'}[weekday]
        is_holiday = jpholiday.is_holiday(d)
        is_saturday = d.weekday() == 5
        is_sunday = d.weekday() == 6
        is_company_holiday = d in company_holiday_dates
        
        # 色の決定
        if is_holiday or is_sunday or is_company_holiday:
            color = 'red'
        elif is_saturday:
            color = 'blue'
        else:
            color = 'black'
            
        day_info[d] = {
            'weekday': weekday_ja,
            'color': color,
            'is_holiday': is_holiday,
            'is_company_holiday': is_company_holiday,
            'company_holiday_name': company_holiday_dates.get(d, '')
        }

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
    shift_types_list = list(ShiftType.objects.all())  # テンプレート用のリスト

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
        'day_info': day_info,
        'employees': employees,
        'shift_dict': shift_dict,
        'shift_types': shift_types,
        'shift_types_list': shift_types_list,  # テンプレート用
        'employee_shifts': employee_shifts,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'show_prev': show_prev,
        'show_next': show_next,
        'min_year': MIN_YEAR,
        'max_year': MAX_YEAR,
        'months': range(1, 13),
    }
    return render(request, 'shift/shift_table.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def save_shift(request):
    """シフト保存API"""
    try:
        data = json.loads(request.body)
        employee_id = data.get('employee_id')
        shift_date = data.get('date')
        shift_type_id = data.get('shift_type_id')
        shift_id = data.get('shift_id')
        
        # バリデーション
        if not employee_id or not shift_date or not shift_type_id:
            return JsonResponse({'success': False, 'error': '必須項目が不足しています'})
        
        # 日付の変換
        try:
            date_obj = date.fromisoformat(shift_date)
        except ValueError:
            return JsonResponse({'success': False, 'error': '無効な日付です'})
        
        # 従業員とシフト種別の存在確認
        try:
            employee = Employee.objects.get(id=employee_id)
            shift_type = ShiftType.objects.get(id=shift_type_id)
        except (Employee.DoesNotExist, ShiftType.DoesNotExist):
            return JsonResponse({'success': False, 'error': '従業員またはシフト種別が見つかりません'})
        
        # シフトの保存または更新
        if shift_id:
            # 更新
            try:
                shift = Shift.objects.get(id=shift_id)
                shift.shift_type = shift_type
                shift.save()
            except Shift.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'シフトが見つかりません'})
        else:
            # 新規作成
            shift, created = Shift.objects.get_or_create(
                employee=employee,
                date=date_obj,
                defaults={'shift_type': shift_type}
            )
            if not created:
                return JsonResponse({'success': False, 'error': '既にシフトが登録されています'})
        
        # 連続勤務日数制限の警告チェック
        warning = shift.check_consecutive_work_days()
        if warning:
            return JsonResponse({
                'success': True, 
                'warning': warning['message']
            })
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '無効なJSONデータです'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def delete_shift(request, shift_id):
    """シフト削除API"""
    try:
        shift = Shift.objects.get(id=shift_id)
        shift.delete()
        return JsonResponse({'success': True})
    except Shift.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'シフトが見つかりません'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
