#!/usr/bin/env python

import setuptools


setuptools.setup(
    name="stacktester",
    version="0.1",
    description="Testing suite for OpenStack software suite.",
    author="Rackspace Titan",
    packages=setuptools.find_packages(),
    scripts=[
        "bin/stacktester",
    ],
    test_suite="nose.collector",
)
