# -*- coding: utf-8 -*-
from email import iterators
from email2pdf2.email2pdf2 import get_input_email
from email.utils import parsedate_to_datetime

import logging
import quopri
import re
import sys
import tzlocal


logger = logging.getLogger("imio.email.parser")


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


def format_date(msg, in_place=False):
    """Format the date in the message to local timezone"""
    date = msg.get("Date")

    if not date:
        logger.error("No date found in message, cannot format date.")
        return "date not found"

    try:
        utc_dt = parsedate_to_datetime(date)
    except ValueError:
        logger.error(f"Invalid date format in message: {date}", exc_info=True)
        formatted_date = date
    else:
        local_tz = tzlocal.get_localzone()
        local_dt = utc_dt.astimezone(local_tz)
        formatted_date = local_dt.strftime("%d-%m-%Y %H:%M:%S")

    if in_place:
        msg.replace_header("Date", formatted_date)
    else:
        return formatted_date
