# -*- coding: utf-8 -*-
from imio.email.parser.tests.test_parser import get_eml_message
from imio.email.parser.utils import decode_quopri  # noqa: F401
from imio.email.parser.utils import format_date
from unittest.mock import patch

import pytz
import unittest


class TestUtils(unittest.TestCase):
    def test_decode_quopri(self):
        to_tests = [
            ("=no_encoding=", "=no_encoding="),
            (
                "=UTF-8QAccus=C3=A9_de_r=C3=A9ception_-_Dossier_complet.pdf=",
                "Accusé_de_réception_-_Dossier_complet.pdf",
            ),
            ("=UTF-8QBonjour=20=20=20=C3=A0 tous!=", "Bonjour   à tous!"),
            ("=ISO-8859-1Q=A1Hola!=", "¡Hola!"),
        ]
        for dic in to_tests:
            self.assertEqual(decode_quopri(dic[0]), dic[1])

    def test_format_date(self):
        name = "01_email_with_inline_and_annexes.eml"
        msg = get_eml_message(name)

        # Test formatting date
        self.assertEqual(msg.get("Date"), "Mon, 06 Jan 2025 09:51:01 +0300")
        self.assertEqual(format_date(msg, in_place=False), "06-01-2025 07:51:01")
        self.assertEqual(msg.get("Date"), "Mon, 06 Jan 2025 09:51:01 +0300")

        # Test in-place formatting
        format_date(msg, in_place=True)
        self.assertEqual(msg.get("Date"), "06-01-2025 07:51:01")

        # Test with different timezones
        msg.replace_header("Date", "Mon, 06 Jan 2025 09:51:01 +0500")
        self.assertEqual(format_date(msg), "06-01-2025 05:51:01")

        # Test with different local timezones
        with patch("tzlocal.get_localzone") as mock_localtime:
            mock_localtime.return_value = pytz.timezone('Europe/Brussels')
            self.assertEqual(format_date(msg), "06-01-2025 05:51:01")
            mock_localtime.return_value = pytz.timezone('UTC')
            self.assertEqual(format_date(msg), "06-01-2025 04:51:01")
            mock_localtime.return_value = pytz.timezone('US/Eastern')
            self.assertEqual(format_date(msg), "05-01-2025 23:51:01")

        # Test with no timezone
        msg.replace_header("Date", "Mon, 06 Jan 2025 09:51:01")
        self.assertEqual(format_date(msg), "06-01-2025 09:51:01")

        # Test with DST offset
        msg.replace_header("Date", "Mon, 06 Jan 2025 09:51:01 +0000")
        self.assertEqual(format_date(msg), "06-01-2025 10:51:01")
        msg.replace_header("Date", "Mon, 06 Aug 2025 09:51:01 +0000")
        self.assertEqual(format_date(msg), "06-08-2025 11:51:01")
        with patch("tzlocal.get_localzone") as mock_localtime:
            mock_localtime.return_value = pytz.timezone('Europe/Brussels')
            self.assertEqual(format_date(msg), "06-08-2025 11:51:01")
            mock_localtime.return_value = pytz.timezone('UTC')
            self.assertEqual(format_date(msg), "06-08-2025 09:51:01")
            mock_localtime.return_value = pytz.timezone('US/Eastern')
            self.assertEqual(format_date(msg), "06-08-2025 05:51:01")

        # An invalid date will leave it untouched
        msg.replace_header("Date", "wrong date format")
        self.assertEqual(format_date(msg), "wrong date format")

        # Test with no date header
        del msg["Date"]
        self.assertEqual(format_date(msg), "date not found")
        format_date(msg, in_place=True)
        self.assertIsNone(msg.get("Date"))
