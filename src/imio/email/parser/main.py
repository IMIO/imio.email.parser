# -*- coding: utf-8 -*-

import imio.email.parser.email2pdf as email2pdf
import os
import six
import sys


def emailtopdf():
    if len(sys.argv) < 2:
        return "You have to pass an eml file"
    proceed, args = email2pdf.handle_args([__file__, '--no-attachments', '--headers', '-i{}'.format(sys.argv[1])])
    input_data = email2pdf.get_input_data(args)
    input_email = email2pdf.get_input_email(input_data)
    payload, parts_already_used = email2pdf.handle_message_body(args, input_email)
    payload = email2pdf.remove_invalid_urls(payload)
    if args.headers:
        header_info = email2pdf.get_formatted_header_info(input_email)
        payload = header_info + payload
    if six.PY3:
        payload = payload.encode("UTF-8")
    output_directory = os.path.normpath(args.output_directory)
    output_file_name = email2pdf.get_output_file_name(args, output_directory)
    email2pdf.output_body_pdf(input_email, payload, output_file_name)
