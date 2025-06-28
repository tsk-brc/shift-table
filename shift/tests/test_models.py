"""
Tests for models.
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from ..models import Employee, ShiftType, CompanyHoliday, LaborLawSettings, Shift
from ..factories import (
    EmployeeFactory, ShiftTypeFactory, WorkShiftTypeFactory, 
    RestShiftTypeFactory, CompanyHolidayFactory, LaborLawSettingsFactory,
    ShiftFactory, RestShiftFactory
)


class EmployeeModelTest(TestCase):
    """Employee model tests."""

    def test_employee_creation(self):
        """Test employee creation."""
        employee = EmployeeFactory()
        self.assertIsNotNone(employee.id)
        self.assertIsInstance(employee.name, str)
        self.assertTrue(len(employee.name) > 0)

    def test_employee_str(self):
        """Test employee string representation."""
        employee = EmployeeFactory(name="田中太郎")
        self.assertEqual(str(employee), "田中太郎")

    def test_employee_verbose_name(self):
        """Test employee verbose names."""
        self.assertEqual(Employee._meta.verbose_name, "従業員")
        self.assertEqual(Employee._meta.verbose_name_plural, "従業員")


class ShiftTypeModelTest(TestCase):
    """ShiftType model tests."""

    def test_shift_type_creation(self):
        """Test shift type creation."""
        shift_type = ShiftTypeFactory()
        self.assertIsNotNone(shift_type.id)
        self.assertIsInstance(shift_type.name, str)
        self.assertIsInstance(shift_type.is_work, bool)
        self.assertIsInstance(shift_type.color, str)

    def test_shift_type_str(self):
        """Test shift type string representation."""
        shift_type = ShiftTypeFactory(name="出勤")
        self.assertEqual(str(shift_type), "出勤")

    def test_shift_type_verbose_name(self):
        """Test shift type verbose names."""
        self.assertEqual(ShiftType._meta.verbose_name, "シフト種別")
        self.assertEqual(ShiftType._meta.verbose_name_plural, "シフト種別")

    def test_work_shift_type(self):
        """Test work shift type."""
        work_shift = WorkShiftTypeFactory()
        self.assertTrue(work_shift.is_work)

    def test_rest_shift_type(self):
        """Test rest shift type."""
        rest_shift = RestShiftTypeFactory()
        self.assertFalse(rest_shift.is_work)

    def test_shift_type_unique_name(self):
        """Test shift type name uniqueness."""
        ShiftTypeFactory(name="出勤")
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            ShiftTypeFactory(name="出勤")


class CompanyHolidayModelTest(TestCase):
    """CompanyHoliday model tests."""

    def test_company_holiday_creation(self):
        """Test company holiday creation."""
        holiday = CompanyHolidayFactory()
        self.assertIsNotNone(holiday.id)
        self.assertIsInstance(holiday.date, date)
        self.assertIsInstance(holiday.name, str)
        self.assertIsInstance(holiday.description, str)

    def test_company_holiday_str(self):
        """Test company holiday string representation."""
        holiday = CompanyHolidayFactory(name="創立記念日")
        self.assertEqual(str(holiday), "創立記念日")

    def test_company_holiday_verbose_name(self):
        """Test company holiday verbose names."""
        self.assertEqual(CompanyHoliday._meta.verbose_name, "会社休日")
        self.assertEqual(CompanyHoliday._meta.verbose_name_plural, "会社休日")

    def test_company_holiday_ordering(self):
        """Test company holiday ordering."""
        holiday1 = CompanyHolidayFactory(date=date(2025, 1, 2))
        holiday2 = CompanyHolidayFactory(date=date(2025, 1, 1))
        holidays = list(CompanyHoliday.objects.all())
        self.assertEqual(holidays[0], holiday2)
        self.assertEqual(holidays[1], holiday1)

    def test_company_holiday_unique_date(self):
        """Test company holiday date uniqueness."""
        CompanyHolidayFactory(date=date(2025, 1, 1))
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            CompanyHolidayFactory(date=date(2025, 1, 1))


class LaborLawSettingsModelTest(TestCase):
    """LaborLawSettings model tests."""

    def test_labor_law_settings_creation(self):
        """Test labor law settings creation."""
        settings = LaborLawSettingsFactory()
        self.assertIsNotNone(settings.id)
        self.assertIsInstance(settings.max_consecutive_work_days, int)
        self.assertIsInstance(settings.min_workers, int)
        self.assertIsNotNone(settings.created_at)
        self.assertIsNotNone(settings.updated_at)

    def test_labor_law_settings_str(self):
        """Test labor law settings string representation."""
        settings = LaborLawSettingsFactory()
        self.assertIn("労働設定", str(settings))

    def test_labor_law_settings_verbose_name(self):
        """Test labor law settings verbose names."""
        self.assertEqual(LaborLawSettings._meta.verbose_name, "労働設定")
        self.assertEqual(LaborLawSettings._meta.verbose_name_plural, "労働設定")

    def test_get_current_settings(self):
        """Test get current settings method."""
        # No settings exist
        settings = LaborLawSettings.get_current_settings()
        self.assertIsNotNone(settings)
        self.assertEqual(settings.max_consecutive_work_days, 6)
        self.assertEqual(settings.min_workers, 1)

        # Settings exist
        custom_settings = LaborLawSettingsFactory(
            max_consecutive_work_days=5,
            min_workers=3
        )
        current_settings = LaborLawSettings.get_current_settings()
        self.assertEqual(current_settings.id, custom_settings.id)
        self.assertEqual(current_settings.max_consecutive_work_days, 5)
        self.assertEqual(current_settings.min_workers, 3)


class ShiftModelTest(TestCase):
    """Shift model tests."""

    def test_shift_creation(self):
        """Test shift creation."""
        shift = ShiftFactory()
        self.assertIsNotNone(shift.id)
        self.assertIsNotNone(shift.employee)
        self.assertIsInstance(shift.date, date)
        self.assertIsNotNone(shift.shift_type)

    def test_shift_str(self):
        """Test shift string representation."""
        employee = EmployeeFactory(name="田中太郎")
        shift_type = ShiftTypeFactory(name="出勤")
        shift = ShiftFactory(employee=employee, shift_type=shift_type)
        expected = f"田中太郎 - {shift.date} - 出勤"
        self.assertEqual(str(shift), expected)

    def test_shift_verbose_name(self):
        """Test shift verbose names."""
        self.assertEqual(Shift._meta.verbose_name, "シフト")
        self.assertEqual(Shift._meta.verbose_name_plural, "シフト")

    def test_shift_unique_together(self):
        """Test shift unique together constraint."""
        employee = EmployeeFactory()
        shift_type = ShiftTypeFactory()
        date_obj = date(2025, 1, 1)
        
        ShiftFactory(employee=employee, shift_type=shift_type, date=date_obj)
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            ShiftFactory(employee=employee, shift_type=shift_type, date=date_obj)

    def test_check_consecutive_work_days_no_warning(self):
        """Test consecutive work days check with no warning."""
        settings = LaborLawSettingsFactory(max_consecutive_work_days=6)
        employee = EmployeeFactory()
        work_shift_type = WorkShiftTypeFactory()
        
        # Create shifts with gaps (no consecutive work days)
        shift1 = ShiftFactory(
            employee=employee,
            shift_type=work_shift_type,
            date=date(2025, 1, 1)
        )
        shift2 = ShiftFactory(
            employee=employee,
            shift_type=work_shift_type,
            date=date(2025, 1, 3)  # Gap of 1 day
        )
        
        warning = shift2.check_consecutive_work_days()
        self.assertIsNone(warning)

    def test_check_consecutive_work_days_with_warning(self):
        """Test consecutive work days check with warning."""
        settings = LaborLawSettingsFactory(max_consecutive_work_days=2)
        employee = EmployeeFactory()
        work_shift_type = WorkShiftTypeFactory()
        
        # Create consecutive work days
        ShiftFactory(
            employee=employee,
            shift_type=work_shift_type,
            date=date(2025, 1, 1)
        )
        ShiftFactory(
            employee=employee,
            shift_type=work_shift_type,
            date=date(2025, 1, 2)
        )
        
        # This should trigger a warning
        shift3 = ShiftFactory(
            employee=employee,
            shift_type=work_shift_type,
            date=date(2025, 1, 3)
        )
        
        warning = shift3.check_consecutive_work_days()
        self.assertIsNotNone(warning)
        self.assertTrue(warning['warning'])
        self.assertIn('連続勤務日数が3日となり', warning['message'])
        self.assertEqual(warning['consecutive_days'], 3)
        self.assertEqual(warning['max_days'], 2)

    def test_check_consecutive_work_days_with_holidays(self):
        """Test consecutive work days check excluding holidays."""
        settings = LaborLawSettingsFactory(max_consecutive_work_days=2)
        employee = EmployeeFactory()
        work_shift_type = WorkShiftTypeFactory()
        rest_shift_type = RestShiftTypeFactory()
        
        # Create shifts with holidays in between
        ShiftFactory(
            employee=employee,
            shift_type=work_shift_type,
            date=date(2025, 1, 1)
        )
        ShiftFactory(
            employee=employee,
            shift_type=rest_shift_type,  # Holiday
            date=date(2025, 1, 2)
        )
        ShiftFactory(
            employee=employee,
            shift_type=work_shift_type,
            date=date(2025, 1, 3)
        )
        
        # This should not trigger a warning because of the holiday
        shift4 = ShiftFactory(
            employee=employee,
            shift_type=work_shift_type,
            date=date(2025, 1, 4)
        )
        
        warning = shift4.check_consecutive_work_days()
        self.assertIsNone(warning)

    def test_check_min_workers_no_warning(self):
        """Test minimum workers check with no warning."""
        settings = LaborLawSettingsFactory(min_workers=2)
        work_shift_type = WorkShiftTypeFactory()
        
        # Create enough workers
        employee1 = EmployeeFactory()
        employee2 = EmployeeFactory()
        ShiftFactory(employee=employee1, shift_type=work_shift_type, date=date(2025, 1, 1))
        ShiftFactory(employee=employee2, shift_type=work_shift_type, date=date(2025, 1, 1))
        
        # This should not trigger a warning
        shift = ShiftFactory(
            employee=EmployeeFactory(),
            shift_type=RestShiftTypeFactory(),  # Rest shift
            date=date(2025, 1, 1)
        )
        
        warning = shift.check_min_workers()
        self.assertIsNone(warning)

    def test_check_min_workers_with_warning(self):
        """Test minimum workers check with warning."""
        settings = LaborLawSettingsFactory(min_workers=2)
        work_shift_type = WorkShiftTypeFactory()
        
        # Create only one worker
        employee1 = EmployeeFactory()
        ShiftFactory(employee=employee1, shift_type=work_shift_type, date=date(2025, 1, 1))
        
        # This should trigger a warning
        shift = ShiftFactory(
            employee=EmployeeFactory(),
            shift_type=RestShiftTypeFactory(),  # Rest shift
            date=date(2025, 1, 1)
        )
        
        warning = shift.check_min_workers()
        self.assertIsNotNone(warning)
        self.assertTrue(warning['warning'])
        self.assertIn('勤務者数が1人となり', warning['message'])
        self.assertEqual(warning['current_workers'], 1)
        self.assertEqual(warning['min_workers'], 2)

    def test_check_min_workers_company_holiday(self):
        """Test minimum workers check on company holiday."""
        settings = LaborLawSettingsFactory(min_workers=2)
        CompanyHolidayFactory(date=date(2025, 1, 1))
        
        # This should not trigger a warning on company holiday
        shift = ShiftFactory(
            employee=EmployeeFactory(),
            shift_type=RestShiftTypeFactory(),
            date=date(2025, 1, 1)
        )
        
        warning = shift.check_min_workers()
        self.assertIsNone(warning)

    def test_check_min_workers_update_scenario(self):
        """Test minimum workers check when updating a shift."""
        settings = LaborLawSettingsFactory(min_workers=2)
        work_shift_type = WorkShiftTypeFactory()
        rest_shift_type = RestShiftTypeFactory()
        
        # Create one worker
        employee1 = EmployeeFactory()
        ShiftFactory(employee=employee1, shift_type=work_shift_type, date=date(2025, 1, 1))
        
        # Create a shift that will be updated
        employee2 = EmployeeFactory()
        shift = ShiftFactory(
            employee=employee2,
            shift_type=work_shift_type,  # Initially work shift
            date=date(2025, 1, 1)
        )
        
        # Update to rest shift - should trigger warning
        shift.shift_type = rest_shift_type
        warning = shift.check_min_workers()
        self.assertIsNotNone(warning)
        self.assertTrue(warning['warning'])
        self.assertIn('勤務者数が1人となり', warning['message'])
        self.assertEqual(warning['current_workers'], 1)

    @pytest.mark.slow
    def test_create_auto_shifts(self):
        """Test auto shift creation."""
        settings = LaborLawSettingsFactory(min_workers=2, max_consecutive_work_days=6)
        employees = [EmployeeFactory() for _ in range(3)]
        work_shift_type = WorkShiftTypeFactory()
        rest_shift_type = RestShiftTypeFactory()
        
        # Create company holiday
        CompanyHolidayFactory(date=date(2025, 1, 15))
        
        result = Shift.create_auto_shifts(2025, 1, 'fill_gaps')
        
        self.assertTrue(result['success'])
        self.assertGreater(result['created_count'], 0)
        self.assertIn('作成し', result['message'])

    def test_create_auto_shifts_no_employees(self):
        """Test auto shift creation with no employees."""
        result = Shift.create_auto_shifts(2025, 1, 'fill_gaps')
        self.assertFalse(result['success'])
        self.assertIn('従業員が登録されていません', result['error'])

    def test_create_auto_shifts_no_work_shift_types(self):
        """Test auto shift creation with no work shift types."""
        EmployeeFactory()
        RestShiftTypeFactory()
        
        result = Shift.create_auto_shifts(2025, 1, 'fill_gaps')
        self.assertFalse(result['success'])
        self.assertIn('勤務シフト種別が登録されていません', result['error'])

    def test_create_auto_shifts_no_rest_shift_type(self):
        """Test auto shift creation with no rest shift type."""
        EmployeeFactory()
        WorkShiftTypeFactory()
        
        result = Shift.create_auto_shifts(2025, 1, 'fill_gaps')
        self.assertFalse(result['success'])
        self.assertIn('休みシフト種別が登録されていません', result['error']) 