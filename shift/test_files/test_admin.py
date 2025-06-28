"""
Tests for admin functionality.
"""

import os
import django
import json
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.admin.sites import site
from ..models import Employee, ShiftType, CompanyHoliday, LaborLawSettings, Shift
from ..admin import (
    EmployeeAdmin, ShiftTypeAdmin, CompanyHolidayAdmin, 
    LaborLawSettingsAdmin, ShiftAdmin
)
from ..factories import (
    EmployeeFactory, ShiftTypeFactory, WorkShiftTypeFactory, 
    RestShiftTypeFactory, CompanyHolidayFactory, LaborLawSettingsFactory,
    ShiftFactory, UserFactory
)

# Django設定を確実に読み込む
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shift_table.settings_test')
django.setup()


class AdminModelTest(TestCase):
    """Admin model tests."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)
        ShiftType.objects.all().delete()

    def test_employee_admin(self):
        """Test employee admin registration."""
        self.assertIn(Employee, site._registry)
        admin = site._registry[Employee]
        self.assertIsInstance(admin, EmployeeAdmin)

    def test_shift_type_admin(self):
        """Test shift type admin registration."""
        self.assertIn(ShiftType, site._registry)
        admin = site._registry[ShiftType]
        self.assertIsInstance(admin, ShiftTypeAdmin)

    def test_company_holiday_admin(self):
        """Test company holiday admin registration."""
        self.assertIn(CompanyHoliday, site._registry)
        admin = site._registry[CompanyHoliday]
        self.assertIsInstance(admin, CompanyHolidayAdmin)

    def test_labor_law_settings_admin(self):
        """Test labor law settings admin registration."""
        self.assertIn(LaborLawSettings, site._registry)
        admin = site._registry[LaborLawSettings]
        self.assertIsInstance(admin, LaborLawSettingsAdmin)

    def test_shift_admin(self):
        """Test shift admin registration."""
        self.assertIn(Shift, site._registry)
        admin = site._registry[Shift]
        self.assertIsInstance(admin, ShiftAdmin)


class AdminViewTest(TestCase):
    """Admin view tests."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)
        ShiftType.objects.all().delete()
        LaborLawSettings.objects.all().delete()

    def test_employee_admin_list_view(self):
        """Test employee admin list view."""
        employee = EmployeeFactory()
        url = reverse('admin:shift_employee_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_shift_type_admin_list_view(self):
        """Test shift type admin list view."""
        shift_type = ShiftTypeFactory(name=f"出勤_{self._testMethodName}")
        url = reverse('admin:shift_shifttype_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_company_holiday_admin_list_view(self):
        """Test company holiday admin list view."""
        holiday = CompanyHolidayFactory()
        url = reverse('admin:shift_companyholiday_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_labor_law_settings_admin_list_view(self):
        """Test labor law settings admin list view."""
        settings = LaborLawSettingsFactory()
        url = reverse('admin:shift_laborlawsettings_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_shift_admin_list_view(self):
        """Test shift admin list view."""
        shift = ShiftFactory()
        url = reverse('admin:shift_shift_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_employee_admin_add_view(self):
        """Test employee admin add view."""
        url = reverse('admin:shift_employee_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_shift_type_admin_add_view(self):
        """Test shift type admin add view."""
        url = reverse('admin:shift_shifttype_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_company_holiday_admin_add_view(self):
        """Test company holiday admin add view."""
        url = reverse('admin:shift_companyholiday_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_labor_law_settings_admin_add_view(self):
        """Test labor law settings admin add view."""
        url = reverse('admin:shift_laborlawsettings_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_shift_admin_add_view(self):
        """Test shift admin add view."""
        url = reverse('admin:shift_shift_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_employee_admin_change_view(self):
        """Test employee admin change view."""
        employee = EmployeeFactory()
        url = reverse('admin:shift_employee_change', args=[employee.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_shift_type_admin_change_view(self):
        """Test shift type admin change view."""
        shift_type = ShiftTypeFactory(name=f"出勤_{self._testMethodName}")
        url = reverse('admin:shift_shifttype_change', args=[shift_type.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_company_holiday_admin_change_view(self):
        """Test company holiday admin change view."""
        holiday = CompanyHolidayFactory()
        url = reverse('admin:shift_companyholiday_change', args=[holiday.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_labor_law_settings_admin_change_view(self):
        """Test labor law settings admin change view."""
        settings = LaborLawSettingsFactory()
        url = reverse('admin:shift_laborlawsettings_change', args=[settings.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_shift_admin_change_view(self):
        """Test shift admin change view."""
        shift = ShiftFactory()
        url = reverse('admin:shift_shift_change', args=[shift.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class CompanyHolidayBulkAddTest(TestCase):
    """Company holiday bulk add tests."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)
        ShiftType.objects.all().delete()
        LaborLawSettings.objects.all().delete()

    def test_bulk_add_view_get(self):
        """Test bulk add view GET request."""
        url = reverse('admin:shift_companyholiday_bulk_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '会社休日一括追加')

    def test_bulk_add_view_post_weekly(self):
        """Test bulk add view POST with weekly holidays."""
        url = reverse('admin:shift_companyholiday_bulk_add')
        data = {
            'holiday_type': 'weekly',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31',
            'weekday': '0',  # 月曜日
            'name': '月曜休日'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_bulk_add_view_post_monthly(self):
        """Test bulk add view POST with monthly holidays."""
        url = reverse('admin:shift_companyholiday_bulk_add')
        data = {
            'holiday_type': 'monthly',
            'day': '15',
            'name': '月次休日'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

    def test_bulk_add_view_post_range(self):
        """Test bulk add view POST with date range holidays."""
        url = reverse('admin:shift_companyholiday_bulk_add')
        data = {
            'holiday_type': 'range',
            'start_date': '2025-01-01',
            'end_date': '2025-01-05',
            'name': '期間休日'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_bulk_add_view_post_single(self):
        """Test bulk add view POST with single holiday."""
        url = reverse('admin:shift_companyholiday_bulk_add')
        data = {
            'holiday_type': 'single',
            'date': '2025-01-01',
            'name': '単日休日'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

    def test_bulk_add_view_post_invalid_data(self):
        """Test bulk add view POST with invalid data."""
        url = reverse('admin:shift_companyholiday_bulk_add')
        data = {
            'holiday_type': 'weekly',
            # 必要なフィールドが不足
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # フォームエラーで再表示


class AutoShiftCreationTest(TestCase):
    """Auto shift creation tests."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)
        ShiftType.objects.all().delete()
        LaborLawSettings.objects.all().delete()

    def test_auto_create_view_get(self):
        """Test auto create view GET request."""
        url = reverse("admin:shift_auto_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '自動シフト作成')

    def test_auto_create_view_post_fill_gaps(self):
        """Test auto create view POST with fill gaps mode."""
        url = reverse("admin:shift_auto_create")
        data = {
            'year': 2025,
            'month': 1,
            'creation_mode': 'fill_gaps'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

    def test_auto_create_view_post_overwrite(self):
        """Test auto create view POST with overwrite mode."""
        url = reverse("admin:shift_auto_create")
        data = {
            'year': 2025,
            'month': 1,
            'creation_mode': 'overwrite'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

    def test_auto_create_view_post_invalid_data(self):
        """Test auto create view POST with invalid data."""
        url = reverse("admin:shift_auto_create")
        data = {
            'year': 2025,
            'month': 13,  # 無効な月
            'creation_mode': 'fill_gaps'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # フォームエラーで再表示 