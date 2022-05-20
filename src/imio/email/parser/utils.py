# -*- coding: utf-8 -*-
from email2pdf2.email2pdf2 import get_input_email


def load_eml_file(filename, encoding='utf8', as_msg=True):
    """Read eml file"""
    with open(filename, "r", encoding=encoding) as input_handle:
        data = input_handle.read()
        if as_msg:
            return get_input_email(data)
        return data
