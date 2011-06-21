#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="stacktester",
    version="0.1",
    description="Testing suite for OpenStack software suite.",
    author="Rackspace Titan",
    packages=find_packages(),
    setup_requires=["nose"],
    test_suite = "nose.collector",
)
