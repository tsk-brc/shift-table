"""
Tests for views.
"""

import json
from datetime import date
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
        shift = ShiftFactory(employee=employee, shift_type=shift_type)
        
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
        self.employee = EmployeeFactory()
        self.shift_type = ShiftTypeFactory()
        self.date = date(2025, 1, 1)

    def test_save_shift_new_shift(self):
        """Test saving a new shift."""
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
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        
        # Check that shift was created
        shift = Shift.objects.get(employee=self.employee, date=self.date)
        self.assertEqual(shift.shift_type, self.shift_type)

    def test_save_shift_update_existing(self):
        """Test updating an existing shift."""
        # Create existing shift
        existing_shift = ShiftFactory(
            employee=self.employee,
            date=self.date,
            shift_type=self.shift_type
        )
        
        new_shift_type = ShiftTypeFactory()
        data = {
            'employee_id': self.employee.id,
            'date': self.date.isoformat(),
            'shift_type_id': new_shift_type.id,
            'shift_id': existing_shift.id
        }
        
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        
        # Check that shift was updated
        existing_shift.refresh_from_db()
        self.assertEqual(existing_shift.shift_type, new_shift_type)

    def test_save_shift_missing_required_fields(self):
        """Test saving shift with missing required fields."""
        data = {
            'employee_id': self.employee.id,
            # Missing date and shift_type_id
        }
        
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('必須項目が不足しています', result['error'])

    def test_save_shift_invalid_date(self):
        """Test saving shift with invalid date."""
        data = {
            'employee_id': self.employee.id,
            'date': 'invalid-date',
            'shift_type_id': self.shift_type.id
        }
        
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('無効な日付です', result['error'])

    def test_save_shift_nonexistent_employee(self):
        """Test saving shift with nonexistent employee."""
        data = {
            'employee_id': 99999,  # Non-existent ID
            'date': self.date.isoformat(),
            'shift_type_id': self.shift_type.id
        }
        
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('従業員またはシフト種別が見つかりません', result['error'])

    def test_save_shift_nonexistent_shift_type(self):
        """Test saving shift with nonexistent shift type."""
        data = {
            'employee_id': self.employee.id,
            'date': self.date.isoformat(),
            'shift_type_id': 99999  # Non-existent ID
        }
        
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('従業員またはシフト種別が見つかりません', result['error'])

    def test_save_shift_duplicate_shift(self):
        """Test saving duplicate shift."""
        # Create existing shift
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
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('既にシフトが登録されています', result['error'])

    def test_save_shift_nonexistent_shift_id(self):
        """Test updating nonexistent shift."""
        data = {
            'employee_id': self.employee.id,
            'date': self.date.isoformat(),
            'shift_type_id': self.shift_type.id,
            'shift_id': 99999  # Non-existent ID
        }
        
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('シフトが見つかりません', result['error'])

    def test_save_shift_consecutive_work_days_warning(self):
        """Test saving shift with consecutive work days warning."""
        settings = LaborLawSettingsFactory(max_consecutive_work_days=2)
        work_shift_type = WorkShiftTypeFactory()
        
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
        
        # Try to create another work day
        data = {
            'employee_id': self.employee.id,
            'date': date(2025, 1, 3).isoformat(),
            'shift_type_id': work_shift_type.id
        }
        
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('warning', result)
        self.assertIn('連続勤務日数が3日となり', result['warning'])

    def test_save_shift_min_workers_warning(self):
        """Test saving shift with minimum workers warning."""
        settings = LaborLawSettingsFactory(min_workers=2)
        work_shift_type = WorkShiftTypeFactory()
        rest_shift_type = RestShiftTypeFactory()
        
        # Create only one worker
        employee1 = EmployeeFactory()
        ShiftFactory(
            employee=employee1,
            shift_type=work_shift_type,
            date=self.date
        )
        
        # Try to create a rest shift
        data = {
            'employee_id': self.employee.id,
            'date': self.date.isoformat(),
            'shift_type_id': rest_shift_type.id
        }
        
        response = self.client.post(
            reverse('save_shift'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('warning', result)
        self.assertIn('勤務者数が1人となり', result['warning'])

    def test_save_shift_force_save(self):
        """Test force saving shift with warnings."""
        settings = LaborLawSettingsFactory(max_consecutive_work_days=2)
        work_shift_type = WorkShiftTypeFactory()
        
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
        self.shift = ShiftFactory()

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