from datetime import datetime
from imio.email.parser.main import main
from unittest.mock import patch

import glob
import os
import PyPDF2
import unittest


EML_TEST_FILES_PATH = os.path.join(os.path.dirname(__file__), "files")


class TestMain(unittest.TestCase):
    @patch("sys.argv", ["main.py", "1", f"{EML_TEST_FILES_PATH}/01_email_with_inline_and_annexes.eml"])
    def test_emailtopdf(self):
        self.assertEqual(main(), None)
        list_of_files = glob.glob("*.pdf")  # * means all if need specific format then *.csv
        latest_file = max(list_of_files, key=os.path.getctime)
        file_creation_time = os.path.getctime(latest_file)
        self.assertTrue((datetime.now().timestamp() - file_creation_time) < 5)

        with open(latest_file, "rb") as f:
            reader = PyPDF2.PdfFileReader(f)
            documentInfo = reader.documentInfo
            self.assertEqual(documentInfo["/Title"], "01 eml")
            self.assertEqual(documentInfo["/Producer"], "email2pdf2")
            self.assertEqual(documentInfo["/Creator"], "wkhtmltopdf 0.12.6")
            self.assertEqual(documentInfo["/Author"], "Stéphan mio <stephan.mio@mail.be>")
            self.assertEqual(reader.getNumPages(), 1)
