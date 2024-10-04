# -*- coding: utf-8 -*-

from email.utils import getaddresses
from imio.email.parser.parser import correct_addresses
from imio.email.parser.parser import Parser

import mailparser
import os
import unittest


def get_eml_message(filename, test_dir=True):
    """Get the disk eml message and return a parsed message object"""
    if test_dir:
        filename = os.path.join(os.path.dirname(__file__), "files", filename)
    return mailparser.parse_from_file(filename)


class TestParser(unittest.TestCase):
    def test_extract_relevant_message(self):
        to_tests = [
            {
                "fn": "01_email_containing_eml.eml",
                "orig": "Agent forward",
                "opl": ["multipart/alternative", "message/rfc822"],
                "opl1": ["multipart/mixed"],
                "ipl": ["multipart/related", "image/png", "application/vnd.oasis.opendocument.text"],
                "msg_s": "Bonjour,\n\nVoici une phrase avec un petit logo [image: image.png] collé dans le texte.",
            },
            {
                "fn": "02_email_containing_eml_containing_eml.eml",
                "orig": "Agent forward",
                "opl": ["multipart/alternative", "message/rfc822"],
                "opl1": ["multipart/mixed"],
                "ipl": ["text/plain", "message/rfc822"],
                "msg_s": "Dear user,",
            },
        ]
        for dic in to_tests:
            name = dic["fn"]
            # with self.subTest(name=name): errors not returned in zc.recipe.testrunner
            oparsed = get_eml_message(name)
            omsg = oparsed.message
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
            ("'xx YY' <xx.yy@DOMAIN.com>", [("'xx YY'", "xx.yy@DOMAIN.com")], [("'xx YY'", "xx.yy@domain.com")]),
            ("xx YY <xx.yy@DOMAIN.com>", [("xx YY", "xx.yy@DOMAIN.com")], [("xx YY", "xx.yy@domain.com")]),
            ('"xx, YY" <xx.yy@DOMAIN.com>', [("xx, YY", "xx.yy@DOMAIN.com")], [("xx, YY", "xx.yy@domain.com")]),
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
                "fn": "01_email_containing_eml.eml",
                "disps": ["inline", "attachment", "attachment"],
                "attachs": ["image.png", "directory_icon.png", "accuse.odt"],
            },
            {"fn": "02_email_containing_eml_containing_eml.eml", "disps": [], "attachs": []},
            {
                "fn": "03_email_with_false_inline.eml",
                "disps": ["inline", "attachment", "attachment"],
                "attachs": ["1624352401933.png", "Erreur 2.jpg", "Erreur 1.png"],
            },
        ]
        for dic in to_tests:
            name = dic["fn"]
            # with self.subTest(name=name): errors not returned in zc.recipe.testrunner
            oparsed = get_eml_message(dic["fn"])
            omsg = oparsed.message
            iparsed = Parser(omsg, False, "1")
            payload, cid_parts_used = iparsed.generate_pdf("/tmp/01.pdf")
            ats = iparsed.attachments(True, cid_parts_used)
            self.assertListEqual([at["filename"] for at in ats], dic["attachs"], name)
            self.assertListEqual([at["disp"] for at in ats], dic["disps"], name)
            ats = iparsed.attachments(False, cid_parts_used)
            self.assertListEqual([at["filename"] for at in ats], dic["attachs"], name)
            self.assertListEqual([at["disp"] for at in ats], dic["disps"], name)
