# -*- coding: utf-8 -*-

import email2pdf
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
    proceed, args = email2pdf.handle_args([__file__, '--no-attachments', '--headers', '-i{}'.format(filename)])
    input_data = email2pdf.get_input_data(args)
    input_email = email2pdf.get_input_email(input_data)
    payload, parts_already_used = email2pdf.handle_message_body(args, input_email)
    payload = email2pdf.remove_invalid_urls(payload)
    if args.headers:
        header_info = email2pdf.get_formatted_header_info(input_email)
        payload = header_info + payload
    payload = payload.encode("UTF-8")
    output_directory = os.path.normpath(args.output_directory)
    output_file_name = email2pdf.get_output_file_name(args, output_directory)
    email2pdf.output_body_pdf(input_email, payload, output_file_name)


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
