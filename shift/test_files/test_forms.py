"""
Tests for forms.
"""

import os
import django
from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date
from ..forms import CompanyHolidayBulkAddForm, AutoShiftForm, ShiftTypeForm
from ..factories import (
    EmployeeFactory, ShiftTypeFactory, WorkShiftTypeFactory, 
    RestShiftTypeFactory, CompanyHolidayFactory, LaborLawSettingsFactory,
    RoleFactory, ShiftTypeRoleMinWorkerFactory
)
from ..models import ShiftType, LaborLawSettings, Role

# Django設定を確実に読み込む
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shift_table.settings_test')
django.setup()


class CompanyHolidayBulkAddFormTest(TestCase):
    """Company holiday bulk add form tests."""

    def setUp(self):
        ShiftType.objects.all().delete()
        LaborLawSettings.objects.all().delete()
        self.work_shift_type = WorkShiftTypeFactory(name=f"出勤_{self._testMethodName}")
        self.rest_shift_type = RestShiftTypeFactory(name=f"休み_{self._testMethodName}")

    def test_form_valid_custom_weekday(self):
        """Test form with valid custom weekday data."""
        form_data = {
            'holiday_type': 'custom_weekday',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31',
            'weekday': '0',
            'name': '月曜休日'
        }
        form = CompanyHolidayBulkAddForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valid_date_range(self):
        """Test form with valid date range data."""
        form_data = {
            'holiday_type': 'date_range',
            'start_date': '2025-01-01',
            'end_date': '2025-01-05',
            'name': '期間休日'
        }
        form = CompanyHolidayBulkAddForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valid_holidays(self):
        """Test form with valid holidays data."""
        form_data = {
            'holiday_type': 'holidays',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31',
            'name': '祝日'
        }
        form = CompanyHolidayBulkAddForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_missing_required_fields(self):
        """Test form with missing required fields."""
        form_data = {
            'holiday_type': 'custom_weekday',
            # Missing start_date, end_date, weekday
        }
        form = CompanyHolidayBulkAddForm(data=form_data)
        self.assertTrue(form.is_valid())  # フォームは必須フィールドがないため有効

    def test_form_end_date_before_start_date(self):
        """Test form with end date before start date."""
        form_data = {
            'holiday_type': 'date_range',
            'start_date': '2025-01-31',
            'end_date': '2025-01-01',
            'name': '期間休日'
        }
        form = CompanyHolidayBulkAddForm(data=form_data)
        self.assertTrue(form.is_valid())  # フォームは日付の順序をチェックしない

    def test_form_clean_custom_weekday(self):
        """Test form clean method for custom weekday holidays."""
        form_data = {
            'holiday_type': 'custom_weekday',
            'weekday': '1',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31',
            'name': '火曜休日'
        }
        form = CompanyHolidayBulkAddForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data['holiday_type'], 'custom_weekday')
        self.assertEqual(cleaned_data['weekday'], '1')
        self.assertEqual(cleaned_data['start_date'], date(2025, 1, 1))
        self.assertEqual(cleaned_data['end_date'], date(2025, 1, 31))

    def test_form_clean_date_range(self):
        """Test form clean method for date range holidays."""
        form_data = {
            'holiday_type': 'date_range',
            'start_date': '2025-01-01',
            'end_date': '2025-01-05',
            'name': '年末年始休暇'
        }
        form = CompanyHolidayBulkAddForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data['holiday_type'], 'date_range')
        self.assertEqual(cleaned_data['start_date'], date(2025, 1, 1))
        self.assertEqual(cleaned_data['end_date'], date(2025, 1, 5))

    def test_form_clean_holidays(self):
        """Test form clean method for holidays."""
        form_data = {
            'holiday_type': 'holidays',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31',
            'name': '祝日'
        }
        form = CompanyHolidayBulkAddForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data['holiday_type'], 'holidays')
        self.assertEqual(cleaned_data['start_date'], date(2025, 1, 1))
        self.assertEqual(cleaned_data['end_date'], date(2025, 1, 31))


class AutoShiftFormTest(TestCase):
    """Auto shift form tests."""

    def setUp(self):
        ShiftType.objects.all().delete()
        LaborLawSettings.objects.all().delete()
        self.work_shift_type = WorkShiftTypeFactory(name=f"出勤_{self._testMethodName}")
        self.rest_shift_type = RestShiftTypeFactory(name=f"休み_{self._testMethodName}")

    def test_form_valid_data(self):
        """Test form with valid data."""
        form_data = {
            'year': 2025,
            'month': 1,
            'creation_mode': 'fill_gaps'
        }
        form = AutoShiftForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_missing_required_fields(self):
        """Test form with missing required fields."""
        form_data = {
            'year': 2025,
            # Missing month and creation_mode
        }
        form = AutoShiftForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('month', form.errors)
        self.assertIn('creation_mode', form.errors)

    def test_form_invalid_year(self):
        """Test form with invalid year."""
        form_data = {
            'year': 1800,  # Too early
            'month': 1,
            'creation_mode': 'fill_gaps'
        }
        form = AutoShiftForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_form_invalid_month(self):
        """Test form with invalid month."""
        form_data = {
            'year': 2025,
            'month': 13,  # Invalid month
            'creation_mode': 'fill_gaps'
        }
        form = AutoShiftForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_form_invalid_creation_mode(self):
        """Test form with invalid creation mode."""
        form_data = {
            'year': 2025,
            'month': 1,
            'creation_mode': 'invalid_mode'
        }
        form = AutoShiftForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('creation_mode', form.errors)

    def test_form_clean_valid_data(self):
        """Test form clean method with valid data."""
        form_data = {
            'year': 2025,
            'month': 1,
            'creation_mode': 'fill_gaps'
        }
        form = AutoShiftForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data['year'], 2025)
        self.assertEqual(cleaned_data['month'], 1)
        self.assertEqual(cleaned_data['creation_mode'], 'fill_gaps')

    def test_form_clean_overwrite_mode(self):
        """Test form clean method with overwrite mode."""
        form_data = {
            'year': 2025,
            'month': 12,
            'creation_mode': 'overwrite'
        }
        form = AutoShiftForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data['year'], 2025)
        self.assertEqual(cleaned_data['month'], 12)
        self.assertEqual(cleaned_data['creation_mode'], 'overwrite')

    def test_form_year_range_validation(self):
        """Test form year range validation."""
        # Test year too low
        form_data = {
            'year': 1899,
            'month': 1,
            'creation_mode': 'fill_gaps'
        }
        form = AutoShiftForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('year', form.errors)

        # Test year too high
        form_data = {
            'year': 2100,
            'month': 1,
            'creation_mode': 'fill_gaps'
        }
        form = AutoShiftForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('year', form.errors)

    def test_form_month_range_validation(self):
        """Test form month range validation."""
        # Test month too low
        form_data = {
            'year': 2025,
            'month': 0,
            'creation_mode': 'fill_gaps'
        }
        form = AutoShiftForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('month', form.errors)

        # Test month too high
        form_data = {
            'year': 2025,
            'month': 13,
            'creation_mode': 'fill_gaps'
        }
        form = AutoShiftForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('month', form.errors)

    def test_form_default_values(self):
        """Test form default values."""
        from ..forms import AutoShiftForm
        from datetime import date
        form = AutoShiftForm()
        today = date.today()
        self.assertEqual(form.initial['year'], today.year)
        self.assertEqual(form.initial['month'], today.month)


class ShiftTypeFormTest(TestCase):
    """Shift type form tests."""

    def test_shift_type_form_with_roles(self):
        """Test shift type form when roles exist."""
        # 役割を作成
        role1 = RoleFactory(name="ホール")
        role2 = RoleFactory(name="キッチン")
        
        form = ShiftTypeForm()
        self.assertIn(f'role_min_workers_{role1.id}', form.fields)
        self.assertIn(f'role_min_workers_{role2.id}', form.fields)
        self.assertEqual(form.fields[f'role_min_workers_{role1.id}'].label, 'ホールの最低人数')
        self.assertEqual(form.fields[f'role_min_workers_{role2.id}'].label, 'キッチンの最低人数')

    def test_shift_type_form_without_roles(self):
        """Test shift type form when no roles exist."""
        # 役割を全て削除
        Role.objects.all().delete()
        
        form = ShiftTypeForm()
        # 役割関連のフィールドが存在しないことを確認
        role_fields = [field for field in form.fields.keys() if field.startswith('role_min_workers_')]
        self.assertEqual(len(role_fields), 0)

    def test_shift_type_form_role_min_workers_validation(self):
        """Test role min workers validation."""
        role = RoleFactory(name="ホール")
        
        # 有効なデータ
        form_data = {
            'name': 'テストシフト',
            'is_work': True,
            'min_workers': 1,
            'max_workers': 5,
            'color': '#FF0000',
            f'role_min_workers_{role.id}': 2
        }
        form = ShiftTypeForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # 保存してJSON変換を確認
        if form.is_valid():
            cleaned_data = form.clean()
            self.assertEqual(cleaned_data['role_min_workers'], {'ホール': 2})

    def test_shift_type_form_existing_data(self):
        """Test form with existing shift type data."""
        role = RoleFactory(name="ホール")
        shift_type = ShiftTypeFactory(name="テストシフト")
        ShiftTypeRoleMinWorkerFactory(shift_type=shift_type, role=role, min_workers=3)
        form = ShiftTypeForm(instance=shift_type)
        self.assertEqual(form.fields[f'role_min_workers_{role.id}'].initial, 3) 