#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 - cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

# crc32
import binascii
import platform
# sha1
import hashlib

class HashCalculator:
    def __init__(self, path):
        self._path = path
        self._algorithms = {}
        self._value = {}

    def register_algorithm(self, algorithm):
        self._algorithms[algorithm.name] = algorithm

    def execute(self):
        if len(self._algorithms) == 0:
            return
        for name in self._algorithms:
            self._value[name] = self._algorithms[name].init_value()
        blocksize = 1024 * 64
        with open(self._path, 'rb') as stream:
            while True:
                buffer = stream.read(blocksize)
                if len(buffer) == 0:
                    break
                for name in self._algorithms:
                    self._value[name] = self._algorithms[name].next_value(buffer, self._value[name])

    def get_result(self, name):
        ''' get result for name. '''
        return self._algorithms[name].to_string(self._value[name])

class HashAlgorithm:
    @property
    def name(self):
        ''' get algorithm name. '''
        raise NotImplementedError

    def init_value(self):
        ''' get algorithm init value. '''
        raise NotImplementedError

    def next_value(self, buffer, last_value):
        ''' get algorithm next value by buffer and last value. '''
        raise NotImplementedError

    def to_string(self, value):
        ''' convert value to upper string. '''
        return ("%08x" % value).upper()

    @classmethod
    def create(cls, name):
        if name == 'crc32':
            return Crc32Algorithm()
        if name == 'sha1':
            return Sha1Algorithm()
        raise NotImplementedError

class Crc32Algorithm(HashAlgorithm):
    def __init__(self):
        py_ver = float(platform.python_version()[0])
        self.need_fix = py_ver < 3

    @property
    def name(self):
        return 'crc32'

    def init_value(self):
        return 0

    def next_value(self, buffer, last_value):
        crc = binascii.crc32(buffer, last_value)
        if self.need_fix:
            crc &= 0xffffffff
        return crc

class Sha1Algorithm(HashAlgorithm):
    @property
    def name(self):
        return 'sha1'

    def init_value(self):
        return hashlib.sha1()

    def next_value(self, buffer, last_value):
        last_value.update(buffer)
        return last_value

    def to_string(self, value):
        return value.hexdigest().upper()

if __name__ == '__main__':
    path = r'__init__.py'
    crc32 = r'7F68B425'
    sha1 = r'C93A9F9AF5AD2D072EB976025ABEDC3EB158608D'
    calc = HashCalculator(path)
    calc.register_algorithm(HashAlgorithm.create('crc32'))
    calc.register_algorithm(HashAlgorithm.create('sha1'))
    calc.execute()
    assert calc.get_result('crc32') == crc32
    assert calc.get_result('sha1') == sha1
    print('test passed.')