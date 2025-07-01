# -*- coding: utf-8 -*-
from email2pdf2 import email2pdf2
from email.message import EmailMessage
from email.utils import getaddresses
from imio.email.parser import email_policy  # noqa
from imio.email.parser.utils import decode_quopri  # noqa
from imio.email.parser.utils import format_date
from imio.email.parser.utils import structure  # noqa
from mailparser.mailparser import MailParser
from mailparser.utils import decode_header_part
from mailparser.utils import ported_string

import base64
import copy
import email
import logging
import os
import re


logger = logging.getLogger("imio.email.parser")

# RFC 2822 local-part: dot-atom or quoted-string
# characters allowed in atom: A-Za-z0-9!#$%&'*+-/=?^_`{|}~
# RFC 2821 domain: max 255 characters
_LOCAL_RE = re.compile(
    r"([A-Za-z0-9!#$%&\'*+\-/=?^_`{|}~]+" r"(\.[A-Za-z0-9!#$%&\'*+\-/=?^_`{|}~]+)*|" r'"[^(\|")]*")@[^@]{3,255}$'
)

# RFC 2821 local-part: max 64 characters
# RFC 2821 domain: sequence of dot-separated labels
# characters allowed in label: A-Za-z0-9-, first is a letter
# Even though the RFC does not allow it all-numeric domains do exist
_DOMAIN_RE = re.compile(r"[^@]{1,64}@[A-Za-z0-9][A-Za-z0-9-]*(\.[A-Za-z0-9][A-Za-z0-9-]*)+$")


def is_email_address(address):
    if _LOCAL_RE.match(address) or _DOMAIN_RE.match(address):
        return True
    return False


def strip_dq(s):
    """Remove the same number of starting and ending double quotes from a string."""
    if not s:
        return s
    start_quotes = 0
    while start_quotes < len(s) and s[start_quotes] == '"':
        start_quotes += 1
    end_quotes = 0
    while end_quotes < len(s) - start_quotes and s[-(end_quotes + 1)] == '"':
        end_quotes += 1
    quotes_to_remove = min(start_quotes, end_quotes)
    if quotes_to_remove > 0:
        return s[quotes_to_remove:-quotes_to_remove] if quotes_to_remove < len(s) else ""
    return s


def correct_addresses(lst):
    """Correct badly handled email. See test_parser...
    Lowercased email."""
    if len(lst) == 1:
        return [(strip_dq(lst[0][0]), lst[0][1].lower())]
    new_lst = []
    new_parts = []
    for tup in lst:
        # not a correct address
        if is_email_address(tup[1]):
            tup = (tup[0], tup[1].lower())
            if new_parts:
                if tup[0]:
                    new_parts.append(tup[0])
                else:
                    logger.warning("part 0 not in tup {} for addresses {}".format(tup, lst))
                new_lst.append((", ".join(new_parts), tup[1]))
                new_parts = []
            else:
                new_lst.append((strip_dq(tup[0]), tup[1]))
        else:
            if tup[0]:
                logger.warning("part 0 in tup {} for addresses {}".format(tup, lst))
            new_parts.append(tup[1])
    return new_lst


class Parser:
    def __init__(self, message, dev_mode, mail_id, extract=True):
        """
        :type message: email.message.Message
        """
        self.initial_message = message
        if extract:
            self.message = self._extract_relevant_message(message)
        else:
            self.message = message
        format_date(self.message, in_place=True)
        self.parsed_message = MailParser(self.message)
        self.dev_mode = dev_mode
        self.mail_id = mail_id
        self.is_default_policy = False
        if isinstance(message, email.message.EmailMessage):
            self.is_default_policy = True
        self._attachments = None

    def _extract_relevant_message(self, message):
        """
        Take the first found EML attachment,
        or use the original message.

        :type message: email.message.Message
        """
        payload = message.get_payload()
        if message.get("X-Forwarded-For") or message.get("X-Forwarded-To") or message.get("Resent-From"):
            self.origin = "Server forward"
            return message
        if type(payload) is list:
            # current transfer
            for part in payload:
                if part.get_content_type() == "message/rfc822":  # maybe also check for attachment filename ?
                    self.origin = "Agent forward"
                    if part.get("Content-Transfer-Encoding") == "base64":  # bluemind in base64
                        return email.message_from_bytes(
                            base64.b64decode(part.get_payload()[0].as_string()), policy=email_policy
                        )
                    return part.get_payload()[0]
            # ibm notes in base64
            if "IBM Notes" in message.get("X-Mailer", ""):
                for part in payload:
                    if (
                        part.get_content_type() == "application/octet-stream"
                        and part.get("Content-Transfer-Encoding") == "base64"
                    ):
                        self.origin = "Agent forward"
                        return email.message_from_bytes(base64.b64decode(part.get_payload()), policy=email_policy)
            # apple mail transfer (combined with the used signature)
            if "Apple Mail" in message.get("X-Mailer", ""):
                for part in payload:
                    if part.get_content_type() == "multipart/mixed":
                        for spart in part.get_payload():
                            if spart.get_content_type() == "message/rfc822":  # maybe check for attachment filename ?
                                self.origin = "Agent forward"
                                return spart.get_payload()[0]
            # owa eml in base64
            for part in payload:
                if (
                    part.get_content_type() == "application/octet-stream"
                    and part.get_content_disposition() == "attachment"
                    and part.get_filename().endswith(".eml")
                    and part.get("Content-Transfer-Encoding") == "base64"
                ):
                    self.origin = "Agent forward"
                    return email.message_from_bytes(base64.b64decode(part.get_payload()), policy=email_policy)

        self.origin = "Generic inbox"
        return message

    @property
    def headers(self):
        if self.is_default_policy:
            headers = {
                "From": correct_addresses(getaddresses(self.message.get("from") and [self.message.get("from")] or [])),
                "To": correct_addresses(getaddresses(self.message.get("to") and [self.message.get("to")] or [])),
                "Cc": correct_addresses(getaddresses(self.message.get("cc") and [self.message.get("cc")] or [])),
                "Subject": self.message.get("subject"),
                "Origin": self.origin,
            }
            if self.origin == "Agent forward":
                headers["Agent"] = correct_addresses(
                    getaddresses(self.initial_message.get("from") and [self.initial_message.get("from")] or [])
                )
        else:
            headers = {
                "From": correct_addresses(self.parsed_message.from_),
                "To": correct_addresses(self.parsed_message.to),
                "Cc": correct_addresses(self.parsed_message.cc),
                "Subject": self.parsed_message.subject,
                "Origin": self.origin,
            }
            if self.origin == "Agent forward":
                headers["Agent"] = correct_addresses(MailParser(self.initial_message).from_)
        return headers

    def get_embedded_images(self):
        payload = self.parsed_message.text_html
        if not payload:
            payload = self.parsed_message.text_plain
        payload = "".join(payload)
        ret = []
        for cid in re.findall(r"cid:([\w_@.-]+)", payload, re.I):
            image_part = email2pdf2.find_part_by_content_id(self.message, cid)
            if image_part is None:
                image_part = email2pdf2.find_part_by_content_type_name(self.message, cid)
            if image_part is not None:
                ret.append(image_part.get("content-id"))
        return ret

    def walk(self, msg_part):
        """Walk over the message tree, yielding each subpart but not walking in contained eml."""
        yield msg_part
        if msg_part.is_multipart() and msg_part.get_content_type() != "message/rfc822":
            for subpart in msg_part.get_payload():
                yield from self.walk(subpart)

    def mailparser_attachments(self):
        """This code comes from mailparser.parse() but with our parser walk()."""
        attachments = []
        for i, p in enumerate(self.walk(self.message)):
            mail_content_type = ported_string(p.get_content_type())
            filename = decode_header_part(p.get_filename())
            content_id = ported_string(p.get("content-id"))
            content_disposition = ported_string(p.get("content-disposition"))
            if not p.is_multipart():
                charset = p.get_content_charset("utf-8")
                charset_raw = p.get_content_charset()
                content_subtype = ported_string(p.get_content_subtype())

                is_attachment = False
                if filename:
                    is_attachment = True
                else:
                    if content_id and content_subtype not in ("html", "plain"):
                        is_attachment = True
                        filename = content_id
                    elif content_subtype in ("rtf",):
                        is_attachment = True
                        filename = f"attachment-{i}.rtf"

                # this is an attachment
                if is_attachment:
                    binary = False
                    transfer_encoding = ported_string(p.get("content-transfer-encoding", "")).lower()
                    # content_disposition = ported_string(p.get("content-disposition"))

                    if transfer_encoding == "base64" or (
                        transfer_encoding == "quoted-printable" and "application" in mail_content_type
                    ):
                        payload = p.get_payload(decode=False)
                        binary = True
                    elif "uuencode" in transfer_encoding:
                        # Re-encode in base64
                        payload = base64.b64encode(p.get_payload(decode=True)).decode("ascii")
                        binary = True
                        transfer_encoding = "base64"
                    else:
                        payload = ported_string(p.get_payload(decode=True), encoding=charset)

                    attachments.append(
                        {
                            "filename": filename,
                            "payload": payload,
                            "binary": binary,
                            "mail_content_type": mail_content_type,
                            "mail_content_subtype": content_subtype,
                            "content-id": content_id,
                            "content-disposition": content_disposition,
                            "charset": charset_raw,
                            "content_transfer_encoding": transfer_encoding,
                        }
                    )
            elif mail_content_type == "message/rfc822":
                # this is an eml attachment
                if not filename and content_id:
                    filename = f"{content_id.strip('<>')}.eml"
                if not filename:
                    filename = f"attachment-{i}.eml"
                raw_file = p.get_payload(0).as_string()
                attachments.append(
                    {
                        "filename": filename,
                        "payload": raw_file,
                        "binary": False,
                        "mail_content_type": mail_content_type,
                        "mail_content_subtype": content_subtype,
                        "content-id": content_id,
                        "content-disposition": content_disposition,
                    }
                )
        return attachments

    @property
    def attachments(self):
        if self._attachments is not None:
            return self._attachments

        em_im = self.get_embedded_images()
        files = []
        for attachment in self.mailparser_attachments():
            # 'content-disposition': 'inline; filename="image001.jpg"'
            # 'content-disposition': 'attachment; filename="Permis de la Parcelle X00.pdf"'
            if attachment["binary"]:
                raw_file = base64.b64decode(attachment["payload"])
            elif isinstance(attachment["payload"], bytes):
                raw_file = attachment["payload"]
            else:
                raw_file = attachment["payload"].encode("utf-8")  # to bytes
            filename = attachment["filename"].replace("\r", "").replace("\n", "")
            filename = filename.replace("<", "").replace(">", "")
            # handle quoted printable filename
            if filename[0] == "=" and filename[-1] == "=":
                filename = decode_quopri(filename)
            if os.path.splitext(filename)[1] == "" and attachment["mail_content_subtype"]:
                filename += "." + attachment["mail_content_subtype"]
            disp = attachment.get("content-disposition", "").split(";")[0]
            if disp not in ("inline", "attachment"):
                logger.error(
                    "{}: attachment with filename '{}' with unknown disposition '{}'".format(
                        self.mail_id, filename, attachment.get("content-disposition", "")
                    )
                )
            if disp == "inline" and attachment["content-id"] not in em_im:
                if self.dev_mode:
                    logger.warning(
                        "{}: inline attachment with filename '{}' not found in embedded".format(self.mail_id, filename)
                    )
                disp = "attachment"
            files.append(
                {
                    "filename": filename,
                    "content": raw_file,
                    "len": len(raw_file),
                    "disp": disp,
                    "type": attachment["mail_content_type"],
                    "cid": attachment["content-id"],
                }
            )

        self._attachments = files
        return files

    def generate_pdf(self, output_path, message=None):
        proceed, args = email2pdf2.handle_args([__file__, "--no-attachments", "--headers"])
        if message is None:
            message = self.message
        copied_message = copy.deepcopy(message)
        try:
            payload, parts_already_used = email2pdf2.handle_message_body(args, copied_message)
        except email2pdf2.FatalException as fe:
            if fe.value == "No body parts found; aborting.":
                self.add_body(copied_message, "<html><body><p></p></body></html>")
                payload, parts_already_used = email2pdf2.handle_message_body(args, copied_message)
            else:
                raise fe
        payload = email2pdf2.remove_invalid_urls(payload)
        if args.headers:
            header_info = email2pdf2.get_formatted_header_info(copied_message)
            payload = header_info + payload
        payload = payload.encode("UTF-8")
        email2pdf2.output_body_pdf(copied_message, payload, output_path)
        return payload, parts_already_used

    def add_body(self, message, body):
        if message.is_multipart():
            alt_msg = EmailMessage()
            alt_msg.set_content(body, subtype="html")
            message.attach(alt_msg)
        else:
            message.set_content(body, subtype="html")
