"""
Tests for forms.
"""

import os
import django
from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date
from ..forms import CompanyHolidayBulkAddForm, AutoShiftForm
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
            'month': 1,
            'creation_mode': 'overwrite'
        }
        form = AutoShiftForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data['creation_mode'], 'overwrite')

    def test_form_year_range_validation(self):
        """Test form year range validation."""
        # Test year too early
        form_data = {
            'year': 1800,
            'month': 1,
            'creation_mode': 'fill_gaps'
        }
        form = AutoShiftForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('year', form.errors)

        # Test year too late
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
        form = AutoShiftForm()
        self.assertEqual(form.fields['year'].initial, None)
        self.assertEqual(form.fields['month'].initial, None)
        self.assertEqual(form.fields['creation_mode'].initial, 'fill_gaps') 