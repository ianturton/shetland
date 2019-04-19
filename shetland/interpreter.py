import os
import readline
import atexit
from .completer import Completer
from lark import Lark, UnexpectedInput
from osgeo import ogr, gdal


class Interpreter:
    drivers = {
        "shp": "ESRI Shapefile", "gpkg": "GPKG"
    }
    vars = {}
    history_file = os.path.join(os.path.expanduser('~'), ".shetland_hist")
    history_length = 1000

    def __init__(self, file="shetland.g"):
        __location__ = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))
        with open(os.path.join(__location__, file)) as f:
            grammar = f.read()

        self.parser = Lark(grammar)
        ogr.UseExceptions()
        gdal.UseExceptions()
        self.setup()

    def setup(self):
        """ Initialization of third-party libraries

        Setting interpreter history.
        Setting appropriate completer function.

        :return:
        """
        if not os.path.exists(self.history_file):
            open(self.history_file, 'a+').close()

        readline.read_history_file(self.history_file)
        readline.set_history_length(self.history_length)
        atexit.register(readline.write_history_file, self.history_file)

        readline.parse_and_bind('set enable-keypad on')

        # TODO find out how to get this list from the grammar
        words = "open", "save", "list", "info", "history", "layer", "print"
        completer = Completer(words)
        readline.set_completer(completer.complete)
        # readline.set_completer_delims(' \t\n;')
        readline.parse_and_bind("tab: complete")

    def run_instruction(self, t):
        print(t)
        args = t.children
        if t.data == 'command':
            for i, c in enumerate(args):
                print(str(i)+" arg: "+c+" "+c.type)
            if (args[0].type == 'VARIABLE'):
                self.vars[args[0].value] = args[2]  # skip =
                return True

            if(len(args) >= 2):  # commands with filename
                res = {
                    'open': self.ogr_open,
                    'save': self.ogr_save,
                    'info': self.ogr_info,
                    'print': self.print_,
                }[args[0]](*args[1:])
            else:
                print("no args "+args[0])
                res = {
                    'list': self.ogr_list,
                    'history': self.history,
                }[args[0]]()
        elif t.data == 'exec':
            res = self.exec_hist(args[1])
        elif t.data == 'repeat':
            count, block = t.children
            for i in range(int(count)):
                res = self.run_instruction(block)
        elif t.data == 'code_block':
            for cmd in t.children:
                res = self.run_instruction(cmd)
        elif t.data == 'instruction':
            print("Instruction "+t.data)
        else:
            raise SyntaxError('Unknown instruction: %s' % t.data)
        return res

    def history(self):
        length = readline.get_current_history_length()
        for i in range(1, length):
            print("%d: %s" % (i, readline.get_history_item(i)))
        return True

    def exec_hist(self, *args):
        val = int(args[0].value)
        cmd = readline.get_history_item(val)
        if cmd:
            length = readline.get_current_history_length() - 1
            readline.replace_history_item(length, cmd)
            return self.run(cmd)
        else:
            raise SyntaxError("Unknown history command %s" % val)

    def print_(self, *args):
        for arg in args:
            var = arg.value
            if var in self.vars:
                print(self.vars.get(var).value)
            else:
                raise SyntaxError('Undefined variable %s' % var)

    def getFileName(self, arg):
        if arg.value in self.vars:
            filename = self.vars.get(arg.value).value
        else:
            filename = arg.strip('"').strip("'")
        return filename

    def ogr_open(self, *args):
        filename = self.getFileName(args[0])
        self.dataSource = ogr.Open(filename, 0)
        if self.dataSource is None:
            print('Could not open %s' % (filename))
            raise IOError("Could not open %s" % (filename))
        else:
            print('Opened %s' % (filename))
            self.filename = filename
            return True

    def ogr_list(self):
        count = self.dataSource.GetLayerCount()
        print("%d layers" % count)
        layers = []
        for i in range(count):
            layer = self.dataSource.GetLayerByIndex(i)
            layers.append(layer)
        layers = sorted(layers, key=lambda x: x.GetName())
        for layer in layers:
            print("Name: %s" % layer.GetName())
        return True

    def ogr_info(self, *args):
        layername = args[0].value
        full = False
        if len(args) > 1:
            full = True
        layer = self.dataSource.GetLayerByName(layername)
        if layer:
            featureCount = layer.GetFeatureCount()
            print("Number of features in  %d" %
                  (featureCount))
            print("BBox: (%f %f), (%f %f)" % layer.GetExtent())
            if full:
                layerDefinition = layer.GetLayerDefn()
                print("Name  -  Type  Width  Precision")
                for i in range(layerDefinition.GetFieldCount()):
                    fieldName = layerDefinition.GetFieldDefn(i).GetName()
                    fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
                    fieldType = layerDefinition.GetFieldDefn(
                        i).GetFieldTypeName(fieldTypeCode)
                    fieldWidth = layerDefinition.GetFieldDefn(i).GetWidth()
                    GetPrecision = layerDefinition.GetFieldDefn(
                        i).GetPrecision()

                    print(fieldName + " - " + fieldType + " " + str(fieldWidth)
                          + " " + str(GetPrecision))
            return True
        else:
            print("%s not found" % layername)
            return False

    def ogr_save(self, *args):
        filename = self.getFileName(args[0])
        idx = filename.rfind(".")
        ext = filename[idx + 1:]
        if len(args) > 1:
            layername = args[1]
        else:
            layername = filename[:idx]

        # look up driver type based on extension
        driverName = self.drivers.get(ext)
        if not driverName:
            print("Unable to find a driver for file '%s'" % ext)
            return
        drv = ogr.GetDriverByName(driverName)
        if os.path.exists(filename):
            drv.DeleteDataSource(filename)

        datasource = drv.CreateDataSource(filename)
        if datasource is not None:
            inlayer = self.dataSource.GetLayerByName(layername)
            datasource.CopyLayer(inlayer, new_name=layername)
            datasource = None  # save!
            return True
        else:
            print("unable to save to %s" % filename)
            return False

    def run(self, program):
        parse_tree = self.parser.parse(program)
        # print(parse_tree.pretty())
        res = False
        for inst in parse_tree.children:
            res = self.run_instruction(inst)
        return res


def main():
    shetland = Interpreter("shetland.g")
    while True:
        try:
            code = input('> ')
            try:
                shetland.run(code)
            except UnexpectedInput as u:
                print("Unexpected input:\n" +
                      u.get_context(code), u.line, u.column)
            except Exception as e:
                print(e)
        except (EOFError, KeyboardInterrupt):
            break


if __name__ == '__main__':
    main()
