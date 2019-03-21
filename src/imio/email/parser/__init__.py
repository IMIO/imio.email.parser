import base64
import email
from mailparser import MailParser


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
        if type(payload) is list:
            for part in payload:
                if part.get_content_type() == 'message/rfc822':  # maybe also check for attachment filename ?
                    return part.get_payload()[0]
        return message

    @property
    def headers(self):
        return {
            'From': self.parsed_message.from_,
            'To': self.parsed_message.to,
            'Subject': self.parsed_message.subject,
        }

    @property
    def attachments(self):
        files = []
        for attachment in self.parsed_message.attachments:
            if attachment['binary']:
                raw_file = base64.b64decode(attachment['payload'])
            else:
                raw_file = attachment['payload'].encode('utf-8')
            files.append({
                'filename': attachment['filename'],
                'content': raw_file,
            })
        return files
