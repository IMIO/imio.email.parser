# -*- coding: utf-8 -*-

from email.mime.text import MIMEText
from email2pdf2 import email2pdf2
import mailparser
import os
import sys


def emailtopdf():
    filename = ''
    if len(sys.argv) == 2:
        if sys.argv[1] in ('1', '2'):
            return "You have to pass an eml file"
        filename = sys.argv[1]
    elif len(sys.argv) == 3:
        filename = sys.argv[2]
    proceed, args = email2pdf2.handle_args([__file__, '--no-attachments', '--headers', '-i{}'.format(filename)])
    input_data = email2pdf2.get_input_data(args)
    input_email = email2pdf2.get_input_email(input_data)
    try:
        payload, parts_already_used = email2pdf2.handle_message_body(args, input_email)
    except email2pdf2.FatalException as fe:
        if fe.value == 'No body parts found; aborting.':
            input_email.attach(MIMEText('<html><body><p></p></body></html>', 'html'))
            payload, parts_already_used = email2pdf2.handle_message_body(args, input_email)
        else:
            raise fe
    payload = email2pdf2.remove_invalid_urls(payload)
    if args.headers:
        header_info = email2pdf2.get_formatted_header_info(input_email)
        payload = header_info + payload
    payload = payload.encode("UTF-8")
    output_directory = os.path.normpath(args.output_directory)
    output_file_name = email2pdf2.get_output_file_name(args, output_directory)
    print(output_file_name)
    email2pdf2.output_body_pdf(input_email, payload, output_file_name)


def parse_eml():
    if len(sys.argv) < 3:
        return "You have to pass an eml file path"
    if not os.path.exists(sys.argv[2]):
        return "The third parameter is not an existing eml file path '{}'".format(sys.argv[2])
    msg = mailparser.parse_from_file(sys.argv[2])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("You have to pass a script choice: 1=emailtopdf, 2=parse_eml")
        sys.exit(0)
    if sys.argv[1] == '1':
        print(emailtopdf())
    elif sys.argv[1] == '2':
        print(parse_eml())
