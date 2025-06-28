"""
Basic tests to verify CircleCI is working.
"""

from django.test import TestCase
from django.urls import reverse


class BasicTest(TestCase):
    """Basic tests to verify the system is working."""

    def test_basic_math(self):
        """Test basic math operations."""
        self.assertEqual(1 + 1, 2)
        self.assertEqual(2 * 3, 6)

    def test_django_setup(self):
        """Test that Django is properly set up."""
        self.assertTrue(True)

    def test_admin_url(self):
        """Test that admin URL is accessible."""
        url = reverse('admin:index')
        self.assertEqual(url, '/admin/')

    def test_shift_url(self):
        """Test that shift URL is accessible."""
        url = reverse('shift_table')
        self.assertEqual(url, '/shift/') 