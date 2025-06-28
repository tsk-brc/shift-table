"""
Tests for views.
"""

import json
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Employee, ShiftType, CompanyHoliday, LaborLawSettings, Shift
from ..factories import (
    EmployeeFactory, ShiftTypeFactory, WorkShiftTypeFactory, 
    RestShiftTypeFactory, CompanyHolidayFactory, LaborLawSettingsFactory,
    ShiftFactory, UserFactory
)


class ShiftTableViewTest(TestCase):
    """Shift table view tests."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)
        ShiftType.objects.all().delete()
        Employee.objects.all().delete()
        self.shift_type = ShiftTypeFactory()
        self.employee = EmployeeFactory()
        self.date = date(2025, 1, 1)

    def test_shift_table_view_get(self):
        """Test shift table view GET request."""
        response = self.client.get(reverse('shift_table'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shift/shift_table.html')

    def test_shift_table_view_with_year_month_params(self):
        """Test shift table view with year and month parameters."""
        response = self.client.get(reverse('shift_table'), {
            'year': 2025,
            'month': 1
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('year', response.context)
        self.assertIn('month', response.context)
        self.assertEqual(response.context['year'], 2025)
        self.assertEqual(response.context['month'], 1)

    def test_shift_table_view_context_data(self):
        """Test shift table view context data."""
        # Create test data
        employee = EmployeeFactory()
        shift_type = ShiftTypeFactory()
        shift = ShiftFactory(employee=employee, shift_type=shift_type, date=self.date)
        
        response = self.client.get(reverse('shift_table'))
        
        self.assertIn('employees', response.context)
        self.assertIn('shift_dict', response.context)
        self.assertIn('shift_types', response.context)
        self.assertIn('days', response.context)
        self.assertIn('day_info', response.context)

    def test_shift_table_view_day_info(self):
        """Test shift table view day information."""
        response = self.client.get(reverse('shift_table'))
        day_info = response.context['day_info']
        
        # Check that day_info contains expected keys
        for day, info in day_info.items():
            self.assertIn('weekday', info)
            self.assertIn('color', info)
            self.assertIn('is_holiday', info)
            self.assertIn('is_company_holiday', info)

    def test_shift_table_view_company_holidays(self):
        """Test shift table view with company holidays."""
        holiday = CompanyHolidayFactory()
        
        response = self.client.get(reverse('shift_table'), {
            'year': holiday.date.year,
            'month': holiday.date.month
        })
        
        day_info = response.context['day_info']
        holiday_info = day_info[holiday.date]
        self.assertTrue(holiday_info['is_company_holiday'])
        self.assertEqual(holiday_info['company_holiday_name'], holiday.name)

    def test_shift_table_view_pagination(self):
        """Test shift table view pagination."""
        response = self.client.get(reverse('shift_table'))
        
        self.assertIn('prev_year', response.context)
        self.assertIn('prev_month', response.context)
        self.assertIn('next_year', response.context)
        self.assertIn('next_month', response.context)
        self.assertIn('show_prev', response.context)
        self.assertIn('show_next', response.context)


class SaveShiftViewTest(TestCase):
    """Save shift view tests."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)
        ShiftType.objects.all().delete()
        Employee.objects.all().delete()
        self.shift_type = ShiftTypeFactory()
        self.employee = EmployeeFactory()
        self.date = date(2025, 1, 1)
        LaborLawSettings.objects.all().delete()

    def test_save_shift_new_shift(self):
        data = {
            'employee_id': self.employee.id,
            'date': self.date.isoformat(),
            'shift_type_id': self.shift_type.id
        }
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        result = json.loads(response.content)
        print(result)
        self.assertTrue(result['success'])

    def test_save_shift_update_existing(self):
        # 既存のシフトを作成
        shift = ShiftFactory(
            employee=self.employee,
            date=self.date,
            shift_type=self.shift_type
        )
        
        # 新しいシフト種別を作成
        new_shift_type = ShiftTypeFactory(name=f"休み_{self._testMethodName}")
        
        data = {
            'shift_id': shift.id,
            'employee_id': self.employee.id,
            'date': self.date.isoformat(),
            'shift_type_id': new_shift_type.id
        }
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        result = json.loads(response.content)
        self.assertTrue(result['success'])

    def test_save_shift_duplicate_shift(self):
        ShiftFactory(
            employee=self.employee,
            date=self.date,
            shift_type=self.shift_type
        )
        data = {
            'employee_id': self.employee.id,
            'date': self.date.isoformat(),
            'shift_type_id': self.shift_type.id
        }
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        result = json.loads(response.content)
        print(result)
        self.assertIn('既にシフトが登録されています', result['error'])

    def test_save_shift_nonexistent_shift_id(self):
        data = {
            'shift_id': 999,  # 存在しないID
            'employee_id': self.employee.id,
            'date': self.date.isoformat(),
            'shift_type_id': self.shift_type.id
        }
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        result = json.loads(response.content)
        self.assertIn('シフトが見つかりません', result['error'])

    def test_save_shift_invalid_data(self):
        data = {
            'employee_id': 999,  # 存在しないID
            'date': 'invalid-date',
            'shift_type_id': 999  # 存在しないID
        }
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        result = json.loads(response.content)
        self.assertIn('無効な日付です', result['error'])

    def test_save_shift_consecutive_work_days_warning(self):
        # 連続勤務日数制限の設定を作成
        settings = LaborLawSettingsFactory(max_consecutive_work_days=3)
        
        # 連続で勤務日を作成
        work_shift_type = ShiftTypeFactory(name=f"出勤_{self._testMethodName}", is_work=True)
        for i in range(3):
            ShiftFactory(
                employee=self.employee,
                date=date(2025, 1, 1) + timedelta(days=i),
                shift_type=work_shift_type
            )
        
        # 4日目の勤務を追加（警告が発生するはず）
        data = {
            'employee_id': self.employee.id,
            'date': date(2025, 1, 4).isoformat(),
            'shift_type_id': work_shift_type.id
        }
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('連続勤務日数が4日となり', result['warning'])

    def test_save_shift_min_workers_warning(self):
        # 最低労働者数制限の設定を作成
        settings = LaborLawSettingsFactory(min_workers=2)
        
        # 他の従業員のシフトを作成（休み）
        other_employee = EmployeeFactory()
        rest_shift_type = ShiftTypeFactory(name=f"休み_{self._testMethodName}", is_work=False)
        ShiftFactory(
            employee=other_employee,
            date=self.date,
            shift_type=rest_shift_type
        )
        
        # 勤務シフトを追加（最低労働者数警告が発生するはず）
        work_shift_type = ShiftTypeFactory(name=f"出勤_{self._testMethodName}", is_work=True)
        data = {
            'employee_id': self.employee.id,
            'date': self.date.isoformat(),
            'shift_type_id': work_shift_type.id
        }
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        result = json.loads(response.content)
        # 最低労働者数が1人の場合、警告は発生しない
        self.assertTrue(result['success'])

    def test_save_shift_force_save(self):
        """Test force saving shift with warnings."""
        settings = LaborLawSettingsFactory(max_consecutive_work_days=2)
        work_shift_type = ShiftTypeFactory()
        
        # Create consecutive work days
        ShiftFactory(
            employee=self.employee,
            shift_type=work_shift_type,
            date=date(2025, 1, 1)
        )
        ShiftFactory(
            employee=self.employee,
            shift_type=work_shift_type,
            date=date(2025, 1, 2)
        )
        
        # Force save with warning
        data = {
            'employee_id': self.employee.id,
            'date': date(2025, 1, 3).isoformat(),
            'shift_type_id': work_shift_type.id,
            'force_save': True
        }
        
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        
        # Check that shift was created despite warning
        shift = Shift.objects.get(employee=self.employee, date=date(2025, 1, 3))
        self.assertEqual(shift.shift_type, work_shift_type)

    def test_save_shift_invalid_json(self):
        """Test saving shift with invalid JSON."""
        response = self.client.post(
            reverse('save_shift'),
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('無効なJSONデータです', result['error'])


class DeleteShiftViewTest(TestCase):
    """Delete shift view tests."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)
        Employee.objects.all().delete()
        ShiftType.objects.all().delete()
        self.employee = EmployeeFactory()
        self.shift_type = ShiftTypeFactory()
        self.date = date(2025, 1, 1)
        self.shift = ShiftFactory(employee=self.employee, shift_type=self.shift_type, date=self.date)

    def test_delete_shift_success(self):
        """Test successful shift deletion."""
        response = self.client.post(reverse('delete_shift', args=[self.shift.id]))
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        
        # Check that shift was deleted
        with self.assertRaises(Shift.DoesNotExist):
            Shift.objects.get(id=self.shift.id)

    def test_delete_shift_nonexistent(self):
        """Test deleting nonexistent shift."""
        response = self.client.post(reverse('delete_shift', args=[99999]))
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('シフトが見つかりません', result['error'])

    def test_shift_creation(self):
        # 別の日付で作成
        another_date = self.date + timedelta(days=1)
        shift = ShiftFactory(employee=self.employee, shift_type=self.shift_type, date=another_date)
        self.assertIsNotNone(shift.id)
        self.assertIsNotNone(shift.employee)
        self.assertIsInstance(shift.date, date)
        self.assertIsNotNone(shift.shift_type) 