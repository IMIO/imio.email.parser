from imio.email.parser.parser import Parser

import mailparser
import os
import unittest


def get_eml_message(filename, test_dir=True):
    """Get the disk eml message and return a parsed message object"""
    if test_dir:
        filename = os.path.join(os.path.dirname(__file__), 'files', filename)
    return mailparser.parse_from_file(filename)


class TestParser(unittest.TestCase):

    def test_extract_relevant_message(self):
        to_tests = [{'fn': '01_email_containing_eml.eml', 'orig': 'Agent forward',
                     'opl': ['multipart/alternative', 'message/rfc822'],
                     'opl1': ['multipart/mixed'],
                     'ipl': ['multipart/related', 'image/png', 'application/vnd.oasis.opendocument.text'],
                     'msg_s': 'Bonjour,\n\nVoici une phrase avec un petit logo [image: image.png] collé dans le texte.',
                     },
                    {'fn': '02_email_containing_eml_containing_eml.eml', 'orig': 'Agent forward',
                     'opl': ['multipart/alternative', 'message/rfc822'],
                     'opl1': ['multipart/mixed'],
                     'ipl': ['text/plain', 'message/rfc822'],
                     'msg_s': 'Dear user,',
                     },
                    ]
        for dic in to_tests:
            name = dic['fn']
            # with self.subTest(name=name): errors not returned in zc.recipe.testrunner
            oparsed = get_eml_message(dic['fn'])
            omsg = oparsed.message
            iparsed = Parser(omsg)
            self.assertEqual(iparsed.origin, dic['orig'], name)
            self.assertListEqual([part.get_content_type() for part in omsg.get_payload()], dic['opl'], name)
            part1 = omsg.get_payload()[1]
            self.assertListEqual([part.get_content_type() for part in part1.get_payload()], dic['opl1'], name)
            self.assertTrue(iparsed.parsed_message.body.startswith(dic['msg_s']), name)
