# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from unittest import TestCase

try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch

from bundlewrap.exceptions import BundleError
from bundlewrap.items import pkg_zypper
from bundlewrap.operations import RunResult


class AskTest(TestCase):
    """
    Tests bundlewrap.items.pkg_zypper.ZypperPkg.ask.
    """
    def test_install(self):
        pkg = pkg_zypper.ZypperPkg(MagicMock(), "foo", {'installed': True})
        status = MagicMock()
        status.info = {'installed': False}
        self.assertEqual(
            pkg.ask(status),
            "status not installed → installed\n",
        )

    def test_remove(self):
        pkg = pkg_zypper.ZypperPkg(MagicMock(), "foo", {'installed': False})
        status = MagicMock()
        status.info = {'installed': True}
        self.assertEqual(
            pkg.ask(status),
            "status installed → not installed\n",
        )


class FixTest(TestCase):
    """
    Tests bundlewrap.items.pkg_zypper.ZypperPkg.fix.
    """
    def test_install(self):
        node = MagicMock()
        pkg = pkg_zypper.ZypperPkg(node, "foo", {'installed': True})
        pkg.fix(MagicMock())

    def test_remove(self):
        node = MagicMock()
        pkg = pkg_zypper.ZypperPkg(node, "foo", {'installed': False})
        pkg.fix(MagicMock())


class GetStatusTest(TestCase):
    """
    Tests bundlewrap.items.pkg_zypper.ZypperPkg.get_status.
    """
    @patch('bundlewrap.items.pkg_zypper.pkg_installed')
    def test_installed_ok(self, pkg_installed):
        pkg = pkg_zypper.ZypperPkg(MagicMock(), "foo", {'installed': True})
        pkg_installed.return_value = True
        status = pkg.get_status()
        self.assertTrue(status.correct)

    @patch('bundlewrap.items.pkg_zypper.pkg_installed')
    def test_not_installed_ok(self, pkg_installed):
        pkg = pkg_zypper.ZypperPkg(MagicMock(), "foo", {'installed': False})
        pkg_installed.return_value = False
        status = pkg.get_status()
        self.assertTrue(status.correct)

    @patch('bundlewrap.items.pkg_zypper.pkg_installed')
    def test_installed_not_ok(self, pkg_installed):
        pkg = pkg_zypper.ZypperPkg(MagicMock(), "foo", {'installed': False})
        pkg_installed.return_value = True
        status = pkg.get_status()
        self.assertFalse(status.correct)

    @patch('bundlewrap.items.pkg_zypper.pkg_installed')
    def test_not_installed_not_ok(self, pkg_installed):
        pkg = pkg_zypper.ZypperPkg(MagicMock(), "foo", {'installed': False})
        pkg_installed.return_value = True
        status = pkg.get_status()
        self.assertFalse(status.correct)


class PkgInstalledTest(TestCase):
    """
    Tests bundlewrap.items.pkg_zypper.pkg_installed.
    """
    def test_installed(self):
        runresult = RunResult()
        runresult.return_code = 0
        runresult.stdout = "Status: install ok installed\n"
        node = MagicMock()
        node.run.return_value = runresult
        self.assertTrue(pkg_zypper.pkg_installed(node, "foo"))

    def test_not_installed(self):
        runresult = RunResult()
        runresult.return_code = 1
        runresult.stdout = "Error: No matching Packages to list\n"
        node = MagicMock()
        node.run.return_value = runresult
        self.assertFalse(pkg_zypper.pkg_installed(node, "foo"))


class ValidateAttributesTest(TestCase):
    """
    Tests bundlewrap.items.pkg_zypper.ZypperPkg.validate_attributes.
    """
    def test_installed_ok(self):
        pkg_zypper.ZypperPkg(MagicMock(), "foo", {'installed': True})
        pkg_zypper.ZypperPkg(MagicMock(), "foo", {'installed': False})

    def test_installed_not_ok(self):
        with self.assertRaises(BundleError):
            pkg_zypper.ZypperPkg(MagicMock(), "foo", {'installed': 0})
        with self.assertRaises(BundleError):
            pkg_zypper.ZypperPkg(MagicMock(), "foo", {'installed': 1})
