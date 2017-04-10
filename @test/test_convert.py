#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import os
import sys
import traceback
import unittest
from jasily.exceptions import ArgumentTypeException
from jasily.convert import *


class TestStringTypeConverter(unittest.TestCase):
    Converter = StringTypeConverter()

    def test_expect_NOT_type(self):
        with self.assertRaises(ArgumentTypeException):
            self.Converter.convert(None, 1)
        with self.assertRaises(ArgumentTypeException):
            self.Converter.convert('None', 1)

    def test_expect_NOT_value(self):
        with self.assertRaises(ArgumentTypeException):
            self.Converter.convert(str, 1)

    def test_expect_NOT_support(self):
        with self.assertRaises(TypeNotSupportException):
            self.Converter.convert(object, '1')

    def test_convert_bool(self):
        self.assertEqual(True, self.Converter.convert(bool, 'true'))
        self.assertEqual(True, self.Converter.convert(bool, '1'))
        self.assertEqual(False, self.Converter.convert(bool, 'false'))
        self.assertEqual(False, self.Converter.convert(bool, '0'))
        with self.assertRaises(TypeConvertException):
            self.assertEqual(False, self.Converter.convert(bool, '2'))

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        unittest.main()
    except Exception:
        traceback.print_exc()
        input()

if __name__ == '__main__':
    main()