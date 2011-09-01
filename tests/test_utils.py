
import datetime
import unittest2 as unittest

from stacktester.common import utils


class ISO8601Test(unittest.TestCase):

    def test_encode(self):
        fixture = '1991-10-13T01:02:03Z'
        actual = utils.load_isotime(fixture)
        expected = datetime.datetime(1991, 10, 13, 01, 02, 03)
        self.assertEqual(actual, expected)

    def test_decode(self):
        fixture = datetime.datetime(1991, 10, 13, 01, 02, 03)
        actual = utils.dump_isotime(fixture)
        expected = '1991-10-13T01:02:03Z'
        self.assertEqual(actual, expected)
