"""
Unit-tests which test the validity of the `stacktester` library.

This file or the directory that it's in should not contain tests which
test an OpenStack installation.
"""

import unittest2 as unittest


class TestTestsRun(unittest.TestCase):
    """Sanity check to make sure that unit-tests are being run."""

    def test_works(self):
        self.assertEquals(True, True)
