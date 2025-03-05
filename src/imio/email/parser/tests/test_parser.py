# -*- coding: utf-8 -*-
from email.utils import getaddresses
from imio.email.parser import email_policy
from imio.email.parser.parser import correct_addresses
from imio.email.parser.parser import Parser

import email
import os
import unittest


def get_eml_message(filename, test_dir=True):
    """Get the disk eml message and return a parsed message object"""
    if test_dir:
        filename = os.path.join(os.path.dirname(__file__), "files", filename)
    with open(filename) as fp:
        return email.message_from_file(fp, policy=email_policy)


class TestParser(unittest.TestCase):
    def test_extract_relevant_message(self):
        to_tests = [
            {
                "fn": "01_email_with_inline_and_annexes.eml",
                "orig": "Agent forward",
                "opl": ["multipart/alternative", "message/rfc822"],
                "opl1": ["multipart/mixed"],
                "msg_s": "Grande image\n[image: LibreOffice_ubuntu.png]\nPetite image\n[image: contact.png]",
            },
            {
                "fn": "02_email_with_inline_annex_eml.eml",
                "orig": "Agent forward",
                "opl": ["multipart/alternative", "message/rfc822"],
                "opl1": ["multipart/mixed"],
                "msg_s": "Autre inline\n[image: organization_icon.png]",
            },
        ]
        for dic in to_tests:
            name = dic["fn"]
            # with self.subTest(name=name): errors not returned in zc.recipe.testrunner
            omsg = get_eml_message(name)
            iparsed = Parser(omsg, False, "1")
            self.assertEqual(iparsed.origin, dic["orig"], name)
            self.assertListEqual([part.get_content_type() for part in omsg.get_payload()], dic["opl"], name)
            part1 = omsg.get_payload()[1]
            self.assertListEqual([part.get_content_type() for part in part1.get_payload()], dic["opl1"], name)
            self.assertTrue(iparsed.parsed_message.body.startswith(dic["msg_s"]), name)

    def test_correct_addresses(self):
        to_tests = [
            ("xx.yy@DOMAIN.com", [("", "xx.yy@DOMAIN.com")], [("", "xx.yy@domain.com")]),
            (" <xx.yy@DOMAIN.com>", [("", "xx.yy@DOMAIN.com")], [("", "xx.yy@domain.com")]),
            ('"xx YY" <xx.yy@DOMAIN.com>', [("xx YY", "xx.yy@DOMAIN.com")], [("xx YY", "xx.yy@domain.com")]),
            ('"\\"xx YY\\"" <xx.yy@DOMAIN.com>', [('"xx YY"', "xx.yy@DOMAIN.com")], [("xx YY", "xx.yy@domain.com")]),
            ("'xx YY' <xx.yy@DOMAIN.com>", [("'xx YY'", "xx.yy@DOMAIN.com")], [("'xx YY'", "xx.yy@domain.com")]),
            ("xx YY <xx.yy@DOMAIN.com>", [("xx YY", "xx.yy@DOMAIN.com")], [("xx YY", "xx.yy@domain.com")]),
            ('"xx, YY" <xx.yy@DOMAIN.com>', [("xx, YY", "xx.yy@DOMAIN.com")], [("xx, YY", "xx.yy@domain.com")]),
            (
                '"aa BB" <aa.bb@SITE.com>, "\\"xx YY\\"" <xx.yy@DOMAIN.com>',
                [("aa BB", "aa.bb@SITE.com"), ('"xx YY"', "xx.yy@DOMAIN.com")],
                [("aa BB", "aa.bb@site.com"), ("xx YY", "xx.yy@domain.com")],
            ),
            ("xx, YY <xx.yy@DOMAIN.com>", [("", "xx"), ("YY", "xx.yy@DOMAIN.com")], [("xx, YY", "xx.yy@domain.com")]),
            (
                "xx, YY,  zz <xx.yy@DOMAIN.com>",
                [("", "xx"), ("", "YY"), ("zz", "xx.yy@DOMAIN.com")],
                [("xx, YY, zz", "xx.yy@domain.com")],
            ),
            # multi values
            (
                "xx.yy@DOMAIN.com, aa.bb@SITE.com",
                [("", "xx.yy@DOMAIN.com"), ("", "aa.bb@SITE.com")],
                [("", "xx.yy@domain.com"), ("", "aa.bb@site.com")],
            ),
            (
                '"xx YY" <xx.yy@DOMAIN.com>, aa.bb@SITE.com',
                [("xx YY", "xx.yy@DOMAIN.com"), ("", "aa.bb@SITE.com")],
                [("xx YY", "xx.yy@domain.com"), ("", "aa.bb@site.com")],
            ),
            (
                'aa.bb@SITE.com, "xx YY" <xx.yy@DOMAIN.com>',
                [("", "aa.bb@SITE.com"), ("xx YY", "xx.yy@DOMAIN.com")],
                [("", "aa.bb@site.com"), ("xx YY", "xx.yy@domain.com")],
            ),
            (
                '"xx YY" <xx.yy@DOMAIN.com>, "aa BB" <aa.bb@SITE.com>',
                [("xx YY", "xx.yy@DOMAIN.com"), ("aa BB", "aa.bb@SITE.com")],
                [("xx YY", "xx.yy@domain.com"), ("aa BB", "aa.bb@site.com")],
            ),
            (
                "xx, YY,  zz <xx.yy@DOMAIN.com>, aa BB <aa.bb@SITE.com>",
                [("", "xx"), ("", "YY"), ("zz", "xx.yy@DOMAIN.com"), ("aa BB", "aa.bb@SITE.com")],
                [("xx, YY, zz", "xx.yy@domain.com"), ("aa BB", "aa.bb@site.com")],
            ),
            (
                "xx, YY,  zz <xx.yy@DOMAIN.com>, aa, BB <aa.bb@SITE.com>",
                [("", "xx"), ("", "YY"), ("zz", "xx.yy@DOMAIN.com"), ("", "aa"), ("BB", "aa.bb@SITE.com")],
                [("xx, YY, zz", "xx.yy@domain.com"), ("aa, BB", "aa.bb@site.com")],
            ),
        ]
        for test in to_tests:
            adr = test[0]
            addresses = getaddresses([adr])
            self.assertListEqual(addresses, test[1], adr)
            self.assertListEqual(correct_addresses(addresses), test[2], adr)

    def test_attachments(self):
        to_tests = [
            {
                "fn": "01_email_with_inline_and_annexes.eml",
                "disps": ["inline", "inline", "attachment", "attachment"],
                "attachs": [
                    "2-1-page-daccueil.png",
                    "contact.png",
                    "accuse.odt",
                    "Capture du 2016-12-12 10-56-00.png",
                ],
            },
            {
                "fn": "02_email_with_inline_annex_eml.eml",
                "disps": ["inline", "attachment", "attachment"],
                "attachs": ["organization_icon.png", "texte_simple ééé.txt", "Email avec inline et annexe.eml"],
            },
            {
                "fn": "03_email_with_false_inline.eml",
                "disps": ["inline", "attachment", "attachment"],
                "attachs": ["1624352401933.png", "Erreur 2.jpg", "Erreur 1.png"],
            },
            {
                "fn": "04_email_with_pdf_attachment.eml",
                "disps": ["attachment"],
                "attachs": ["pdf-example-bookmarks-1-2.pdf"],
            },
        ]
        for dic in to_tests:
            name = dic["fn"]
            # with self.subTest(name=name): errors not returned in zc.recipe.testrunner
            omsg = get_eml_message(dic["fn"])
            iparsed = Parser(omsg, False, "1")
            # payload, cid_parts_used = iparsed.generate_pdf("/tmp/01.pdf")
            ats = iparsed.attachments
            self.assertListEqual([at["filename"] for at in ats], dic["attachs"], name)
            self.assertListEqual([at["disp"] for at in ats], dic["disps"], name)

    def test_add_body(self):
        message = get_eml_message("01_email_with_inline_and_annexes.eml")
        parser = Parser(message, False, "1")
        self.assertEqual(len(message.get_payload()), 2)

        parser.add_body(message, "hello world")
        self.assertEqual(len(message.get_payload()), 3)
        self.assertEqual(message.get_payload(2).get_content(), "hello world\n")
        self.assertEqual(message.get_payload(2).get_content_type(), "text/html")
