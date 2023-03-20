#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys

with open("README.md", "r") as fh:
    long_description = fh.read()


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name="stockrec",
    version="0.0.1",
    author="Magnus Runesson",
    author_email="M.Runesson@gmail.se",
    description="Scraping forecasts from Avanza website.",
    url="https://github.com/M.Runesson/stockrec",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache 2.0",
    entry_points='''
        [console_scripts]
        stockrec=stockrec.cli
    ''',
    data_files=[],
    packages=find_packages(),
    install_requires=['requests',
                      'beautifulsoup4',
                      'pg8000',
                      'fire'],
    tests_require=['pytest',
                   'nose'],
    test_suite='tests',
    cmdclass={'test': PyTest},
    include_package_data=True,
    classifiers=(
        "Environment :: Console",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Database",
        "Topic :: Utilities"
    ),
)
