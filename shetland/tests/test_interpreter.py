import pytest
import os
from shetland.interpreter import Interpreter


class TestInterprester:

    THIS_DIR = os.path.dirname(os.path.abspath(__file__))

    def setup_method(self, method):
        interpreter = Interpreter()
        self.drivers = interpreter.drivers
        self.run = interpreter.run
        self.data_path = os.path.normpath(
            os.path.join(self.THIS_DIR, os.pardir, 'tests/data/'))

    def test_open(self):
        code = "open '%s/states.%s'"
        for ext in self.drivers.keys():
            c = code % (self.data_path, ext)
            print("testing "+c)
            assert self.run(c) is True

    def test_open_missing_shp(self):
        for ext in self.drivers.keys():
            with pytest.raises(IOError):
                self.run("open '%s/missing.%s'" % (self.data_path, ext))

    def test_list_layers(self):
        code = """open '%s/states.shp'
        list"""
        assert self.run(code % self.data_path) is True

    def test_list_info(self):
        code = """open '%s/states.%s'
                  list
                  info states"""
        for ext in self.drivers.keys():
            assert self.run(code % (self.data_path, ext)) is True

    def test_save(self):
        code = """open '%s/states.shp'
            save '/tmp/ian.shp' states
            """
        assert self.run(code % self.data_path) is True

    def test_variables(self):
        code = """a=/tmp/ian.shp"""
        assert self.run(code) is True
