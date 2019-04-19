import pytest
from shetland.interpreter import Interpreter


class TestInterprester:

    def setup_method(self, method):
        interpreter = Interpreter()
        self.run = interpreter.run

    def test_open(self):
        code = "open '/home/ian/Data/states/states.%s'"
        for ext in ("shp", "gpkg"):
            assert self.run(code % (ext)) is True
        code = "open /home/ian/Data/states/states.%s"
        for ext in ("shp", "gpkg"):
            assert self.run(code % (ext)) is True

    def test_open_missing_shp(self):
        with pytest.raises(IOError):
            self.run("open '/home/ian/Data/states/missing.shp'")
        with pytest.raises(IOError):
            self.run("open /home/ian/Data/states/missing.shp")

    def test_list_layers(self):
        code = """open '/home/ian/Data/states/states.shp'
        list"""
        assert self.run(code) is True

    def test_list_info(self):
        code = """open '/home/ian/Data/states/states.%s'
                  list
                  info states"""
        for ext in ("shp", "gpkg"):
            assert self.run(code % (ext)) is True

    def test_save(self):
        code = """open '/home/ian/Data/states/states.shp'
            save '/tmp/ian.shp' states
            """
        assert self.run(code) is True

    def test_variables(self):
        code = """a=/tmp/ian.shp"""
        assert self.run(code) is True
