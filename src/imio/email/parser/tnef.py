# -*- coding: utf-8 -*-
from datetime import timezone
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import format_datetime
from imio.email.parser import email_policy
from tnefparse import properties as props
from tnefparse import TNEF

import email
import logging
import mimetypes


logger = logging.getLogger("imio.email.parser")

CONTENT_TYPES = ("application/ms-tnef", "application/vnd.ms-tnef")

_BODY_HEADERS = (
    "content-type",
    "content-transfer-encoding",
    "content-disposition",
    "content-language",
    "mime-version",
)


def _prop(mapi_attrs, prop_id):
    """Return the value of a MAPI property, or None when it is absent."""
    for attr in mapi_attrs or []:
        if attr.name == prop_id:
            return attr.data
    return None


def _file_infos(attachment):
    """Return the filename and the split content type of a TNEF attachment."""
    name = _prop(attachment.mapi_attrs, props.MAPI_ATTACH_LONG_FILENAME) or attachment.name or "attachment"
    content_type = (
        _prop(attachment.mapi_attrs, props.MAPI_ATTACH_MIME_TAG)
        or mimetypes.guess_type(name)[0]
        or "application/octet-stream"
    )
    maintype, _, subtype = content_type.partition("/")
    return name, maintype, subtype


def _headers(tnef_msg, mail_id):
    """Rebuild the header block of a TNEF encapsulated message."""
    msg = EmailMessage(policy=email_policy)
    raw = _prop(tnef_msg.mapiprops, props.MAPI_TRANSPORT_MESSAGE_HEADERS)
    if raw:
        for name, value in email.message_from_string(raw, policy=email_policy).items():
            if name.lower() not in _BODY_HEADERS:
                msg[name] = value
        return msg
    # a mail composed inside Exchange never went through a transport, so it has no
    # header block to copy: rebuild what the MAPI properties give us.
    logger.warning("%s: TNEF message without transport headers, using MAPI properties", mail_id)
    address = _prop(tnef_msg.mapiprops, props.MAPI_SENDER_EMAIL_ADDRESS)
    if address:
        msg["From"] = Address(_prop(tnef_msg.mapiprops, props.MAPI_SENDER_NAME) or "", addr_spec=address)
    subject = _prop(tnef_msg.mapiprops, props.MAPI_SUBJECT)
    if subject:
        msg["Subject"] = subject
    sent = _prop(tnef_msg.mapiprops, props.MAPI_CLIENT_SUBMIT_TIME)
    if sent:
        msg["Date"] = format_datetime(sent.replace(tzinfo=timezone.utc))
    # no To header: MAPI_DISPLAY_TO holds display names, not addresses
    return msg


def _build(tnef_msg, mail_id):
    """Turn one TNEF stream into an email message.

    :type tnef_msg: tnefparse.tnef.TNEF
    :rtype: email.message.EmailMessage
    """
    msg = _headers(tnef_msg, mail_id)
    if tnef_msg.htmlbody:
        msg.set_content(tnef_msg.htmlbody, subtype="html")
    elif tnef_msg.body:
        msg.set_content(tnef_msg.body)
    else:
        # a body stored as compressed rtf only (PR_RTF_COMPRESSED) ends up here
        logger.warning("%s: TNEF message without html or plain body", mail_id)
        msg.set_content("")
    # inline parts first: add_related wraps the body in multipart/related and
    # add_attachment then wraps that in multipart/mixed. The other order nests wrongly.
    for attachment in tnef_msg.attachments:
        cid = _prop(attachment.mapi_attrs, props.MAPI_ATTACH_CONTENT_ID)
        if not cid:
            continue
        name, maintype, subtype = _file_infos(attachment)
        # disposition is explicit: giving only a filename would make it an attachment
        msg.add_related(
            attachment.data,
            maintype,
            subtype,
            cid="<{}>".format(cid.strip("<>")),
            disposition="inline",
            filename=name,
        )
    for attachment in tnef_msg.attachments:
        if _prop(attachment.mapi_attrs, props.MAPI_ATTACH_CONTENT_ID):
            continue  # already added above as an inline part
        if getattr(attachment, "embed", None) is not None:
            # a mail attached to the mail we are rebuilding
            name = attachment.long_filename() or attachment.name or "attachment"
            if not name.lower().endswith(".eml"):
                name = "{}.eml".format(name)
            msg.add_attachment(_build(attachment.embed, mail_id), filename=name)
            continue
        name, maintype, subtype = _file_infos(attachment)
        msg.add_attachment(attachment.data, maintype, subtype, filename=name)
    return msg


def extract_forwarded_message(payload, mail_id=""):
    """Return the email attached inside a winmail.dat TNEF part, or None.

    None means the part carries no attached email, so the caller keeps its usual
    handling: such a mail is not an agent forward.

    :param payload: decoded bytes of the application/ms-tnef part
    :rtype: email.message.EmailMessage or None
    """
    try:
        tnef_msg = TNEF(payload)
    except Exception:
        logger.error("%s: cannot read the winmail.dat tnef part", mail_id, exc_info=True)
        return None
    for attachment in tnef_msg.attachments:
        if getattr(attachment, "embed", None) is not None:
            return _build(attachment.embed, mail_id)
    return None
