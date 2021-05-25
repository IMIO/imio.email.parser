=================
imio.email.parser
=================

This package can parse emails and generate a PDF file of their content.

It is mainly used by package `imio.email.dms`.


Features
--------

1. select relevant email messages (e.g. email forwarded as an attachment)
2. parse emails (headers, attachments, ...)
3. generate a PDF email preview with email2pdf package


Usage
-----

.. code-block:: python

    mail = email.message_from_string(mail_body)
    parser = Parser(mail)
    print(parser.headers)
    print(parser.attachments)
    parser.generate_pdf(pdf_path)


Requirements
------------

package wkhtmltopdf


Contribute
----------

- Issue Tracker: https://github.com/IMIO/imio.email.parser/issues
- Source Code: https://github.com/IMIO/imio.email.parser


License
-------

The project is licensed under the GPLv2.
