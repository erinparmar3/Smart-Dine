"""
Compatibility test module so that `python manage.py test`
can import the label ``smartdine.smartdine`` without errors.

Real tests should live in app-specific ``tests.py`` files.
"""

from django.test import TestCase


class SmokeTests(TestCase):
    def test_project_imports(self):
        """Basic smoke test that the Django project imports."""
        self.assertTrue(True)

