# -*- coding: utf-8 -*-

from email2pdf2 import cmd
from email2pdf2 import email2pdf2
from email.mime.text import MIMEText
from imio.email.parser.utils import load_eml_file  # noqa
from imio.email.parser.utils import stop  # noqa

import mailparser
import os
import sys


def emailtopdf():
    filename = ""
    if len(sys.argv) == 2:
        stop("You have to pass an eml file")
    elif len(sys.argv) == 3:
        filename = sys.argv[2]
    _, args = email2pdf2.handle_args([__file__, "--no-attachments", "--headers", "-i{}".format(filename)])
    input_data = email2pdf2.get_input_data(args)
    input_email = email2pdf2.get_input_email(input_data)
    try:
        payload, _ = email2pdf2.handle_message_body(args, input_email)
    except email2pdf2.FatalException as fe:
        if fe.value == "No body parts found; aborting.":
            input_email.attach(MIMEText("<html><body><p></p></body></html>", "html"))
            payload, _ = email2pdf2.handle_message_body(args, input_email)
        else:
            raise fe
    payload = email2pdf2.remove_invalid_urls(payload)
    if args.headers:
        header_info = email2pdf2.get_formatted_header_info(input_email)
        payload = header_info + payload
    payload = payload.encode("UTF-8")
    output_directory = os.path.normpath(args.output_directory)
    output_file_name = email2pdf2.get_output_file_name(args, output_directory)
    print("Generated pdf '{}'".format(output_file_name))
    email2pdf2.output_body_pdf(input_email, payload, output_file_name)


def emailtopdf_main():
    if len(sys.argv) == 2:
        stop("You have to pass email2pdf2 options, like -i xx.eml --headers --no-attachments")
    sys.argv.pop(1)  # remove this script option
    cmd.main()


def parse_eml():
    if len(sys.argv) < 3:
        stop("You have to pass an eml file path")
    if not os.path.exists(sys.argv[2]):
        stop("The third parameter is not an existing eml file path '{}'".format(sys.argv[2]))
    # test with mailparser
    msg = mailparser.parse_from_file(sys.argv[2])
    msg.attachments  # not correct: an eml is not considered as attachment
    # test with email
    msg = load_eml_file(sys.argv[2])
    # parts = email2pdf2.find_all_attachments(msg, [])  not correct
    email2pdf2.handle_attachments(msg, ".", True, False, [])  # bool= prefix date, ignore_floating_attachments


def main():
    if len(sys.argv) < 2:
        stop("You have to pass a script choice: 1=emailtopdf, 2=parse_eml, 3=emailtopdf_main")
    if sys.argv[1] == "1":
        emailtopdf()
    elif sys.argv[1] == "2":
        parse_eml()
    elif sys.argv[1] == "3":
        emailtopdf_main()


if __name__ == "__main__":
    main()
