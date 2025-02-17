# -*- coding: utf-8 -*-
from imio.email.parser.utils import decode_quopri  # noqa: F401

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
