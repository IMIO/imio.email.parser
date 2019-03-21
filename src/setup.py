from setuptools import setup

setup(
    name='imio.email.parser',
    version='0.1.dev0',
    packages=['imio', 'imio.email', 'imio.email.parser'],
    package_dir={'': 'src'},
    url='https://pypi.org/project/imio.email.parser',
    license='GPL',
    author='Nicolas Demonté',
    author_email='support@imio.be',
    description='',
    install_requires=[
        'mailparser',
    ],
)
