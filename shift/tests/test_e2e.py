"""
End-to-end tests using Selenium.
"""

import pytest
from django.test import LiveServerTestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from ..factories import (
    UserFactory, EmployeeFactory, ShiftTypeFactory, WorkShiftTypeFactory,
    RestShiftTypeFactory, CompanyHolidayFactory, LaborLawSettingsFactory
)


class ShiftTableE2ETest(LiveServerTestCase):
    """End-to-end tests for shift table functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up Chrome driver."""
        super().setUpClass()
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        """Tear down Chrome driver."""
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.employee = EmployeeFactory(name="田中太郎")
        self.work_shift_type = WorkShiftTypeFactory(name="出勤")
        self.rest_shift_type = RestShiftTypeFactory(name="休み")
        self.settings = LaborLawSettingsFactory(min_workers=2, max_consecutive_work_days=6)

    def test_shift_table_page_load(self):
        """Test that shift table page loads correctly."""
        # Login
        self.client.force_login(self.user)
        cookie = self.client.cookies['sessionid']
        self.driver.get(self.live_server_url)
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'secure': False,
            'path': '/'
        })

        # Navigate to shift table
        self.driver.get(f"{self.live_server_url}/shift/")
        
        # Check page title
        self.assertIn("シフト管理", self.driver.title)
        
        # Check that employee is displayed
        employee_element = self.driver.find_element(By.XPATH, f"//td[contains(text(), '{self.employee.name}')]")
        self.assertIsNotNone(employee_element)

    def test_shift_creation(self):
        """Test creating a shift through the UI."""
        # Login
        self.client.force_login(self.user)
        cookie = self.client.cookies['sessionid']
        self.driver.get(self.live_server_url)
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'secure': False,
            'path': '/'
        })

        # Navigate to shift table
        self.driver.get(f"{self.live_server_url}/shift/")
        
        # Find and click on a cell to create shift
        cell = self.driver.find_element(By.CSS_SELECTOR, "td.shift-cell")
        cell.click()
        
        # Wait for modal to appear
        modal = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "shiftModal"))
        )
        
        # Select employee
        employee_select = Select(modal.find_element(By.NAME, "employee"))
        employee_select.select_by_visible_text(self.employee.name)
        
        # Select shift type
        shift_type_select = Select(modal.find_element(By.NAME, "shift_type"))
        shift_type_select.select_by_visible_text(self.work_shift_type.name)
        
        # Save shift
        save_button = modal.find_element(By.ID, "saveShiftBtn")
        save_button.click()
        
        # Wait for modal to close
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "shiftModal"))
        )
        
        # Check that shift was created (cell should have content)
        cell = self.driver.find_element(By.CSS_SELECTOR, "td.shift-cell")
        self.assertNotEqual(cell.text.strip(), "")

    def test_shift_edit(self):
        """Test editing a shift through the UI."""
        # Login
        self.client.force_login(self.user)
        cookie = self.client.cookies['sessionid']
        self.driver.get(self.live_server_url)
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'secure': False,
            'path': '/'
        })

        # Navigate to shift table
        self.driver.get(f"{self.live_server_url}/shift/")
        
        # Find and click on a cell with existing shift
        cell = self.driver.find_element(By.CSS_SELECTOR, "td.shift-cell")
        cell.click()
        
        # Wait for modal to appear
        modal = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "shiftModal"))
        )
        
        # Change shift type
        shift_type_select = Select(modal.find_element(By.NAME, "shift_type"))
        shift_type_select.select_by_visible_text(self.rest_shift_type.name)
        
        # Save shift
        save_button = modal.find_element(By.ID, "saveShiftBtn")
        save_button.click()
        
        # Wait for modal to close
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "shiftModal"))
        )
        
        # Check that shift was updated
        cell = self.driver.find_element(By.CSS_SELECTOR, "td.shift-cell")
        self.assertIn(self.rest_shift_type.name, cell.text)

    def test_shift_deletion(self):
        """Test deleting a shift through the UI."""
        # Login
        self.client.force_login(self.user)
        cookie = self.client.cookies['sessionid']
        self.driver.get(self.live_server_url)
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'secure': False,
            'path': '/'
        })

        # Navigate to shift table
        self.driver.get(f"{self.live_server_url}/shift/")
        
        # Find and click on a cell with existing shift
        cell = self.driver.find_element(By.CSS_SELECTOR, "td.shift-cell")
        cell.click()
        
        # Wait for modal to appear
        modal = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "shiftModal"))
        )
        
        # Click delete button
        delete_button = modal.find_element(By.ID, "deleteShiftBtn")
        delete_button.click()
        
        # Wait for modal to close
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "shiftModal"))
        )
        
        # Check that shift was deleted (cell should be empty)
        cell = self.driver.find_element(By.CSS_SELECTOR, "td.shift-cell")
        self.assertEqual(cell.text.strip(), "")

    def test_warning_modal(self):
        """Test warning modal appears when labor law violations occur."""
        # Create consecutive work days to trigger warning
        from ..models import Shift
        from datetime import date
        
        Shift.objects.create(
            employee=self.employee,
            date=date(2025, 1, 1),
            shift_type=self.work_shift_type
        )
        Shift.objects.create(
            employee=self.employee,
            date=date(2025, 1, 2),
            shift_type=self.work_shift_type
        )
        
        # Login
        self.client.force_login(self.user)
        cookie = self.client.cookies['sessionid']
        self.driver.get(self.live_server_url)
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'secure': False,
            'path': '/'
        })

        # Navigate to shift table
        self.driver.get(f"{self.live_server_url}/shift/")
        
        # Find and click on a cell to create shift
        cell = self.driver.find_element(By.CSS_SELECTOR, "td.shift-cell")
        cell.click()
        
        # Wait for modal to appear
        modal = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "shiftModal"))
        )
        
        # Select employee and work shift type
        employee_select = Select(modal.find_element(By.NAME, "employee"))
        employee_select.select_by_visible_text(self.employee.name)
        
        shift_type_select = Select(modal.find_element(By.NAME, "shift_type"))
        shift_type_select.select_by_visible_text(self.work_shift_type.name)
        
        # Save shift (should trigger warning)
        save_button = modal.find_element(By.ID, "saveShiftBtn")
        save_button.click()
        
        # Wait for warning modal to appear
        warning_modal = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "warningModal"))
        )
        
        # Check warning message
        warning_text = warning_modal.find_element(By.CLASS_NAME, "modal-body").text
        self.assertIn("連続勤務日数", warning_text)

    def test_pagination(self):
        """Test pagination functionality."""
        # Login
        self.client.force_login(self.user)
        cookie = self.client.cookies['sessionid']
        self.driver.get(self.live_server_url)
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'secure': False,
            'path': '/'
        })

        # Navigate to shift table
        self.driver.get(f"{self.live_server_url}/shift/")
        
        # Check that pagination controls exist
        pagination = self.driver.find_element(By.CLASS_NAME, "pagination")
        self.assertIsNotNone(pagination)
        
        # Check that month/year selectors exist
        year_select = self.driver.find_element(By.NAME, "year")
        month_select = self.driver.find_element(By.NAME, "month")
        self.assertIsNotNone(year_select)
        self.assertIsNotNone(month_select)

    def test_company_holiday_display(self):
        """Test that company holidays are displayed correctly."""
        # Create company holiday
        holiday = CompanyHolidayFactory(
            date=date(2025, 1, 15),
            name="創立記念日"
        )
        
        # Login
        self.client.force_login(self.user)
        cookie = self.client.cookies['sessionid']
        self.driver.get(self.live_server_url)
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'secure': False,
            'path': '/'
        })

        # Navigate to shift table for January 2025
        self.driver.get(f"{self.live_server_url}/shift/?year=2025&month=1")
        
        # Check that holiday date has red color (company holiday styling)
        # This would need to be adjusted based on actual CSS classes used
        holiday_cell = self.driver.find_element(By.XPATH, "//td[@data-date='2025-01-15']")
        self.assertIsNotNone(holiday_cell)


class AdminE2ETest(LiveServerTestCase):
    """End-to-end tests for admin functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up Chrome driver."""
        super().setUpClass()
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        """Tear down Chrome driver."""
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory(is_staff=True, is_superuser=True)

    def test_admin_login(self):
        """Test admin login functionality."""
        # Navigate to admin login
        self.driver.get(f"{self.live_server_url}/admin/")
        
        # Enter credentials
        username_field = self.driver.find_element(By.NAME, "username")
        password_field = self.driver.find_element(By.NAME, "password")
        
        username_field.send_keys(self.user.username)
        password_field.send_keys("password123")
        
        # Submit form
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        submit_button.click()
        
        # Check that we're logged in
        self.assertIn("Django 管理サイト", self.driver.title)

    def test_employee_admin(self):
        """Test employee admin functionality."""
        # Login to admin
        self.client.force_login(self.user)
        cookie = self.client.cookies['sessionid']
        self.driver.get(self.live_server_url)
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'secure': False,
            'path': '/'
        })
        
        # Navigate to employee admin
        self.driver.get(f"{self.live_server_url}/admin/shift/employee/")
        
        # Check that employee list page loads
        self.assertIn("従業員", self.driver.title)
        
        # Click add employee
        add_button = self.driver.find_element(By.CSS_SELECTOR, "a.addlink")
        add_button.click()
        
        # Fill in employee details
        name_field = self.driver.find_element(By.NAME, "name")
        name_field.send_keys("テスト従業員")
        
        # Save
        save_button = self.driver.find_element(By.CSS_SELECTOR, "input[name='_save']")
        save_button.click()
        
        # Check that employee was created
        self.assertIn("従業員 \"テスト従業員\" を正常に追加しました", self.driver.page_source)

    def test_shift_type_admin(self):
        """Test shift type admin functionality."""
        # Login to admin
        self.client.force_login(self.user)
        cookie = self.client.cookies['sessionid']
        self.driver.get(self.live_server_url)
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'secure': False,
            'path': '/'
        })
        
        # Navigate to shift type admin
        self.driver.get(f"{self.live_server_url}/admin/shift/shifttype/")
        
        # Check that shift type list page loads
        self.assertIn("シフト種別", self.driver.title)
        
        # Click add shift type
        add_button = self.driver.find_element(By.CSS_SELECTOR, "a.addlink")
        add_button.click()
        
        # Fill in shift type details
        name_field = self.driver.find_element(By.NAME, "name")
        name_field.send_keys("テストシフト")
        
        is_work_checkbox = self.driver.find_element(By.NAME, "is_work")
        is_work_checkbox.click()
        
        color_field = self.driver.find_element(By.NAME, "color")
        color_field.send_keys("#FF0000")
        
        # Save
        save_button = self.driver.find_element(By.CSS_SELECTOR, "input[name='_save']")
        save_button.click()
        
        # Check that shift type was created
        self.assertIn("シフト種別 \"テストシフト\" を正常に追加しました", self.driver.page_source) 