import pytest
import os
import readline
from shetland.interpreter import Interpreter
import lark


class TestInterpreter:

    THIS_DIR = os.path.dirname(os.path.abspath(__file__))

    def setup_method(self, method):
        self.interpreter = Interpreter()
        self.drivers = self.interpreter.drivers
        self.run = self.interpreter.run
        self.data_path = os.path.normpath(
            os.path.join(self.THIS_DIR, os.pardir, 'tests/data/'))

    def test_unknown(self):
        with pytest.raises(lark.exceptions.ParseError):
            self.run("unknown")

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

    def test_variable_filename(self):
        """
        make sure that the " are stripped from the file name
        when it is fetched from the variable
        """
        code = """a="ian.shp"
            open a
        """
        with pytest.raises(IOError) as ex:
            self.run(code)
        assert '"' not in str(ex.value)

    def test_for_loop_glob(self):
        code = """for i in **/data/* {
            print i
        }"""
        assert self.run(code) is True

    def test_for_loop_one(self):
        code = """for i in %s/states.shp {
            print i
        }"""
        assert self.run(code % self.data_path) is True

    def test_for_loop_list(self):
        code = """b="fred.shp"
        for i in ["a",b,"Color"] {
            print i
        }
        """
        assert self.run(code) is True

    def test_history(self):
        # code = """history"""
        # assert self.run(code) is True
        code = """a=/tmp/ian.shp"""
        assert self.run(code) is True
        readline.write_history_file()
        code = """!!"""
        assert self.run(code) is True
        length = self.interpreter.getHistoryLength()
        if length > 2:
            val = length - 2
            code = "!%d" % val
            assert self.run(code) is True
