import base64
import email
import six

from mailparser import MailParser
import imio.email.parser.email2pdf as email2pdf


class Parser:
    def __init__(self, message):
        """
        :type message: email.message.Message
        """
        self.initial_message = message
        self.message = self._extract_relevant_message(message)
        self.parsed_message = MailParser(self.message)

    def _extract_relevant_message(self, message):
        """
        Take the first found EML attachment,
        or use the original message.

        :type message: email.message.Message
        """
        payload = message.get_payload()
        if message.get("X-Forwarded-For") or message.get("X-Forwarded-To"):
            self.origin = "Server forward"
            return message
        if type(payload) is list:
            for part in payload:
                if (
                    part.get_content_type() == "message/rfc822"
                ):  # maybe also check for attachment filename ?
                    self.origin = "Agent forward"
                    return part.get_payload()[0]
        self.origin = "Generic inbox"
        return message

    @property
    def headers(self):
        headers = {
            "From": self.parsed_message.from_,
            "To": self.parsed_message.to,
            "Cc": self.parsed_message.cc,
            "Subject": self.parsed_message.subject,
            "Origin": self.origin,
        }
        if self.origin == 'Agent forward':
            headers['Agent'] = MailParser(self.initial_message).from_
        return headers

    @property
    def attachments(self):
        files = []
        for attachment in self.parsed_message.attachments:
            if attachment["binary"]:
                raw_file = base64.b64decode(attachment["payload"])
            else:
                raw_file = attachment["payload"].encode("utf-8")
            files.append({"filename": attachment["filename"], "content": raw_file})
        return files

    def generate_pdf(self, output_path):
        proceed, args = email2pdf.handle_args([__file__, "--no-attachments", '--headers'])
        payload, parts_already_used = email2pdf.handle_message_body(args, self.message)
        payload = email2pdf.remove_invalid_urls(payload)
        if args.headers:
            header_info = email2pdf.get_formatted_header_info(self.message)
            payload = header_info + payload
        if six.PY3:
            payload = payload.encode("UTF-8")
        email2pdf.output_body_pdf(self.message, payload, output_path)
