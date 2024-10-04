# -*- coding: utf-8 -*-
from email import generator
from email import iterators
from email2pdf2.email2pdf2 import get_input_email
from io import BytesIO
from mailparser.utils import decode_header_part
from mailparser.utils import ported_string
from mailparser.utils import random_string
from pathvalidate import sanitize_filename

import base64
import mimetypes
import os
import sys


def load_eml_file(filename, encoding="utf8", as_msg=True):
    """Read eml file"""
    with open(filename, "r", encoding=encoding) as input_handle:
        data = input_handle.read()
        if as_msg:
            return get_input_email(data)
        return data


def attachment_infos(attach):
    content_id = ported_string(attach.get("content-id"))
    content_disposition = ported_string(attach.get("content-disposition"))
    mail_content_type = ported_string(attach.get_content_type())
    filename = decode_header_part(attach.get_filename())
    if not filename:
        ext = mimetypes.guess_extension(mail_content_type)
        if content_id:
            filename = "{}{}".format(sanitize_filename(content_id), ext)
        else:
            filename = "{}{}".format(random_string(), ext)
    transfer_encoding = ported_string(attach.get("content-transfer-encoding", "")).lower()
    charset = attach.get_content_charset("utf-8")
    charset_raw = attach.get_content_charset()
    binary = False
    if mail_content_type == "message/rfc822":
        # structure(attach)
        fp = BytesIO()
        gen = generator.BytesGenerator(fp)
        content = attach.get_payload()
        if isinstance(content, list) and len(content) == 1:
            content = content[0]
        gen.flatten(content)
        fp.seek(0)
        payload = fp.read()
        fp.close()
    elif transfer_encoding == "base64" or (
        transfer_encoding == "quoted-printable" and "application" in mail_content_type
    ):
        payload = attach.get_payload(decode=False)
        binary = True
    elif "uuencode" in transfer_encoding:
        # Re-encode in base64
        payload = base64.b64encode(attach.get_payload(decode=True)).decode("ascii")
        binary = True
        transfer_encoding = "base64"
    else:
        payload = ported_string(attach.get_payload(decode=True), encoding=charset)

    return {
        "filename": filename,
        "payload": payload,
        "binary": binary,
        "mail_content_type": mail_content_type,
        "content-id": content_id,
        "content-disposition": content_disposition,
        "charset": charset_raw,
        "content_transfer_encoding": transfer_encoding,
    }


def stop(msg, logger=None):
    if logger:
        logger.error(msg)
    else:
        print(msg)
    sys.exit(0)


def structure(msg):
    iterators._structure(msg)
