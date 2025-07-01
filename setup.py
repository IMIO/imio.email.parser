# -*- coding: utf-8 -*-

from setuptools import setup


long_description = "\n\n".join(
    [
        open("README.rst").read(),
        open("CONTRIBUTORS.rst").read(),
        open("CHANGES.rst").read(),
    ]
)


setup(
    name="imio.email.parser",
    version="0.3.3",
    packages=["imio", "imio.email", "imio.email.parser"],
    package_dir={"": "src"},
    url="https://pypi.org/project/imio.email.parser",
    license="GPL",
    author="Nicolas Demonté",
    author_email="support@imio.be",
    description="This parser extracts forwarded attached email, embedded images and attachments. "
    "It also generates a PDF from the email.",
    keywords="email parser pdf attachment",
    long_description=long_description,
    classifiers=[
        "Environment :: Console",
        "Environment :: No Input/Output (Daemon)",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    python_requires=">=3.10, <3.11",
    install_requires=[
        "mail-parser",
        "beautifulsoup4>=4.6.3",
        "email2pdf2",
        "html5lib",
        "lxml",
        "pathvalidate",
        "pypdf2",
        "python-magic",
        "reportlab",
        "requests",
        "six",
        "tzlocal",
    ],
    entry_points="""
    [console_scripts]
    emailtopdf = imio.email.parser.main:main
    """,
)
