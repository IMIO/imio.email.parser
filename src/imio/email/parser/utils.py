# -*- coding: utf-8 -*-
from email import iterators
from email2pdf2.email2pdf2 import get_input_email

import quopri
import re
import sys


def decode_quopri(encoded_string):
    """Decode eventually quoted-printable encoded string"""
    match = re.match(r"=(?P<encoding>[^Qq]*)[Qq](?P<encoded>.*)=$", encoded_string)
    if not match:
        return encoded_string
    encoding = match.group("encoding").lower()
    encoded_part = match.group("encoded")
    decoded_bytes = quopri.decodestring(encoded_part)
    try:
        return decoded_bytes.decode(encoding)
    except LookupError:
        # Si l'encodage n'est pas reconnu, on suppose UTF-8 par défaut
        return decoded_bytes.decode("utf-8")


def load_eml_file(filename, encoding="utf8", as_msg=True):
    """Read eml file"""
    with open(filename, "r", encoding=encoding) as input_handle:
        data = input_handle.read()
        if as_msg:
            return get_input_email(data)
        return data


def stop(msg, logger=None):
    if logger:
        logger.error(msg)
    else:
        print(msg)
    sys.exit(0)


def structure(msg):
    iterators._structure(msg)
