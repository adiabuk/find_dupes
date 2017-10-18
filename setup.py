#!/usr/bin/env python

"""
Setup script for find_dupes - a puplicate file finder
"""

from setuptools import setup

with open('requirements.txt', 'r') as reqs_file:
    REQS = reqs_file.readlines()
VER = '0.1'
NAME = 'find_dupes'

setup(
    name=NAME,
    packages=[NAME],
    version=VER,
    description='a duplicate file finder',
    author='Amro Diab',
    author_email='adiab@linuxmail.org',
    url='https://github.com/adiabuk/find_dupes',
    download_url=('https://github.com/adiabuk/find_dupes/archive/{0}.tar.gz'
                  .format(VER)),
    keywords=['finddups', 'files', 'dups', 'duplicates'],
    install_requires=REQS,
    entry_points={'console_scripts':['find_dupes=find_dupes.find_dupes:main']},
    test_suite=None,
    classifiers=[],
)
