import pytest
import tempfile
import os
import shutil
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
        self.out_path = os.path.normpath(tempfile.mkdtemp(
            prefix="shetland"))

    def teardown_method(self, method):
        shutil.rmtree(self.out_path)

    def test_unknown(self):
        with pytest.raises(lark.exceptions.ParseError):
            self.run("unknown")

    def test_open(self):
        code = "open '%s/states.%s'"
        for ext in self.drivers.keys():
            c = code % (self.data_path, ext)
            assert self.run(c)

    def test_open_no_quote(self):
        code = "open %s/states.%s"
        for ext in self.drivers.keys():
            c = code % (self.data_path, ext)
            assert self.run(c)

    def test_open_to_var(self):
        code = """a = open '%s/states.shp'
        print a
        """
        result = self.run(code % (self.data_path))
        print(self.interpreter.vars['a'])
        assert result is True

    def test_open_missing_shp(self):
        for ext in self.drivers.keys():
            with pytest.raises(IOError):
                self.run("open '%s/missing.%s'" % (self.data_path, ext))

    def test_list_layers(self):
        code = """open '%s/states.shp'
        list"""
        assert self.run(code % self.data_path)

    def test_list_layers_from_var(self):
        code = """a = open '%s/states.shp'
        open '%s/states.gpkg'
        list a"""
        assert self.run(code % (self.data_path, self.data_path))

    def test_list_layers_to_var(self):
        code = """
        a = open '%s/states.gpkg'
        b = list a
        for i in b {
            print i
        }"""
        assert self.run(code % (self.data_path))

    def test_list_info(self):
        code = """open '%s/states.%s'
                  list
                  info states"""
        for ext in self.drivers.keys():
            assert self.run(code % (self.data_path, ext)) is True

    def test_list_info_var(self):
        code = """a = open '%s/states.gpkg'
                  b = list a
                  for x in b {
                    info x
                  }"""
        assert self.run(code % (self.data_path)) is True

    def test_save(self):
        code = """open '%s/states.shp'
            save '%s/ian.shp' states
            """
        assert self.run(code % (self.data_path, self.out_path)) is True

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

    def test_simple_copy(self):
        code = "copy %s/states.shp states to %s/copy1.shp"
        assert self.run(code % (self.data_path, self.out_path)) is True
        code = """open %s/copy1.shp
        list
        info copy1 full
        """
        assert self.run(code % (self.out_path)) is True
