#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
import mock

from napixd.exceptions import ValidationError
from napixd.managers.validators.list import Map, not_empty


class Test_not_empty(unittest.TestCase):
    def test_is_empty(self):
        self.assertRaises(ValidationError, not_empty, [])

    def test_is_not_empty(self):
        self.assertEqual(not_empty([1, 2]), [1, 2])


class TestMap(unittest.TestCase):
    def setUp(self):
        self.v1 = mock.Mock()
        self.v2 = mock.Mock()
        self.validators = [self.v1, self.v2]

    def map(self):
        return Map(*self.validators)

    def validate(self, values):
        m = self.map()
        return m(values)

    def test_map_good(self):
        self.v1.side_effect = (1).__add__
        self.v2.side_effect = (2).__mul__

        self.assertEqual(self.validate([1, 2, 3]), [4, 6, 8])

    def test_map_bad(self):
        self.v1.side_effect = ValidationError('OH SNAP :(')

        try:
            self.validate([1, 2, 3])
        except ValidationError as ve:
            self.assertEqual(dict(ve), {
                0: ValidationError('OH SNAP :('),
                1: ValidationError('OH SNAP :('),
                2: ValidationError('OH SNAP :('),
            })
        except Exception as e:
            self.fail('Unexpected %s', e)
        else:
            self.fail('ValidationError not raised')

        self.assertEqual(self.v2.call_count, 0)

    def test_map_some(self):
        def v2(x):
            if x & 1:
                return 2 * x
            raise ValidationError('OH SNAP :(')

        self.v1.side_effect = lambda x: x
        self.v2.side_effect = v2

        try:
            self.validate([1, 2, 3])
        except ValidationError as ve:
            self.assertEqual(dict(ve), {
                1: ValidationError('OH SNAP :('),
            })
        except Exception as e:
            self.fail('Unexpected {0}'.format(e))
        else:
            self.fail('ValidationError not raised')

    def test_doctstring(self):
        def a():
            pass

        def b():
            '''this and that'''
            pass

        self.validators = [a, b]
        self.assertEqual(self.map().__doc__, 'a\n\nthis and that')
