"""
Tests for models.
"""

import os
import django
import pytest
from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError

# Django設定を確実に読み込む
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shift_table.settings_test')
django.setup()

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

    def setUp(self):
        ShiftType.objects.all().delete()

    def test_shift_type_creation(self):
        """Test shift type creation."""
        shift_type = ShiftTypeFactory()
        self.assertIsNotNone(shift_type.id)
        self.assertIsInstance(shift_type.name, str)
        self.assertIsInstance(shift_type.is_work, bool)
        self.assertIsInstance(shift_type.color, str)

    def test_shift_type_str(self):
        """Test shift type string representation."""
        shift_type = ShiftTypeFactory(name=f"出勤_{self._testMethodName}")
        self.assertIn("出勤", str(shift_type))

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
        ShiftTypeFactory(name=f"出勤_{self._testMethodName}")
        with self.assertRaises(Exception):
            ShiftTypeFactory(name=f"出勤_{self._testMethodName}")


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
        self.assertIn("創立記念日", str(holiday))

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

    def setUp(self):
        LaborLawSettings.objects.all().delete()

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
        self.assertIn("最大連続勤務日数", str(settings))
        self.assertIn("最低労働者数", str(settings))

    def test_labor_law_settings_verbose_name(self):
        """Test labor law settings verbose names."""
        self.assertEqual(LaborLawSettings._meta.verbose_name, "労働設定")
        self.assertEqual(LaborLawSettings._meta.verbose_name_plural, "労働設定")

    def test_labor_law_settings_max_consecutive_work_days(self):
        settings = LaborLawSettingsFactory(max_consecutive_work_days=5)
        self.assertEqual(settings.max_consecutive_work_days, 5)

    def test_labor_law_settings_min_workers(self):
        settings = LaborLawSettingsFactory(min_workers=3)
        self.assertEqual(settings.min_workers, 3)

    def test_get_current_settings(self):
        # 既存の設定をクリア
        LaborLawSettings.objects.all().delete()
        
        # 新しい設定を作成
        settings = LaborLawSettingsFactory()
        current_settings = LaborLawSettings.get_current_settings()
        self.assertEqual(current_settings, settings)

    def test_get_current_settings_creates_default(self):
        # 既存の設定をクリア
        LaborLawSettings.objects.all().delete()
        
        # 設定が存在しない場合、デフォルト設定が作成される
        current_settings = LaborLawSettings.get_current_settings()
        self.assertIsNotNone(current_settings)
        self.assertEqual(current_settings.max_consecutive_work_days, 6)
        self.assertEqual(current_settings.min_workers, 1)


class ShiftModelTest(TestCase):
    """Shift model tests."""

    def setUp(self):
        ShiftType.objects.all().delete()

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
        shift_type = ShiftTypeFactory(name=f"出勤_{self._testMethodName}")
        shift = ShiftFactory(employee=employee, shift_type=shift_type)
        self.assertIn("田中太郎", str(shift))
        self.assertIn("出勤", str(shift))

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

    def test_shift_employee_relationship(self):
        employee = EmployeeFactory()
        shift_type = ShiftTypeFactory(name=f"出勤_{self._testMethodName}")
        shift = ShiftFactory(employee=employee, shift_type=shift_type)
        self.assertEqual(shift.employee, employee)

    def test_shift_shift_type_relationship(self):
        employee = EmployeeFactory()
        shift_type = ShiftTypeFactory(name=f"出勤_{self._testMethodName}")
        shift = ShiftFactory(employee=employee, shift_type=shift_type)
        self.assertEqual(shift.shift_type, shift_type)

    def test_shift_date_field(self):
        employee = EmployeeFactory()
        shift_type = ShiftTypeFactory(name=f"出勤_{self._testMethodName}")
        test_date = date(2025, 1, 1)
        shift = ShiftFactory(employee=employee, shift_type=shift_type, date=test_date)
        self.assertEqual(shift.date, test_date)

    @pytest.mark.slow
    def test_create_auto_shifts_min_workers_compliance(self):
        """Test that auto shift creation respects minimum workers requirement."""
        settings = LaborLawSettingsFactory(min_workers=2, max_consecutive_work_days=6)
        employees = [EmployeeFactory() for _ in range(3)]
        work_shift_type = WorkShiftTypeFactory()
        rest_shift_type = RestShiftTypeFactory()
        
        # Create auto shifts
        result = Shift.create_auto_shifts(2025, 1, 'overwrite')
        
        self.assertTrue(result['success'])
        self.assertGreater(result['created_count'], 0)
        
        # Check that each day has at least min_workers working
        for day in range(1, 32):
            try:
                target_date = date(2025, 1, day)
                work_shifts = Shift.objects.filter(
                    date=target_date,
                    shift_type__is_work=True
                )
                work_count = work_shifts.count()
                
                # Skip company holidays
                company_holiday = CompanyHoliday.objects.filter(date=target_date).first()
                if company_holiday:
                    continue
                
                # Check minimum workers requirement
                self.assertGreaterEqual(
                    work_count, 
                    settings.min_workers,
                    f"Day {day} has only {work_count} workers, but minimum is {settings.min_workers}"
                )
            except ValueError:
                # Skip invalid dates (e.g., February 30th)
                continue

    @pytest.mark.slow
    def test_create_auto_shifts_consecutive_work_days_override(self):
        """Test that auto shift creation overrides consecutive work days when needed for minimum workers."""
        settings = LaborLawSettingsFactory(min_workers=2, max_consecutive_work_days=3)
        employees = [EmployeeFactory() for _ in range(2)]
        work_shift_type = WorkShiftTypeFactory()
        rest_shift_type = RestShiftTypeFactory()
        
        # Create shifts for previous days to force consecutive work days limit
        for day in range(28, 32):  # December 28-31
            try:
                prev_date = date(2024, 12, day)
                for employee in employees:
                    ShiftFactory(
                        employee=employee,
                        shift_type=work_shift_type,
                        date=prev_date
                    )
            except ValueError:
                continue
        
        # Create auto shifts for January
        result = Shift.create_auto_shifts(2025, 1, 'overwrite')
        
        self.assertTrue(result['success'])
        
        # Check that minimum workers requirement is still met even with consecutive work days limit
        for day in range(1, 5):  # Check first few days
            try:
                target_date = date(2025, 1, day)
                work_shifts = Shift.objects.filter(
                    date=target_date,
                    shift_type__is_work=True
                )
                work_count = work_shifts.count()
                
                # Skip company holidays
                company_holiday = CompanyHoliday.objects.filter(date=target_date).first()
                if company_holiday:
                    continue
                
                # Should still meet minimum workers requirement
                self.assertGreaterEqual(
                    work_count, 
                    settings.min_workers,
                    f"Day {day} has only {work_count} workers, but minimum is {settings.min_workers}"
                )
            except ValueError:
                continue 