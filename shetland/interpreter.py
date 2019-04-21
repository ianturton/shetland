import os

from pathlib import Path
import readline
import atexit
from .completer import Completer
from lark import Lark, UnexpectedInput
from lark.lexer import Token
from osgeo import ogr, gdal


class Interpreter:
    drivers = {
        "shp": "ESRI Shapefile",
        "gpkg": "GPKG",
        "json": "GeoJSON",
        "geojson": "GeoJSON",
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
        self.__setup()

    def __setup(self):
        """
        Setting interpreter history.
        Setting appropriate completer function.

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

    def assignVar(self, name, val):
        """
        Assign a value to a variable
        """
        # print("setting "+name+" to "+val)
        self.vars[name] = val

    @classmethod
    def getHistoryLength(cls):
        """
        only really needed for testing
        """
        return readline.get_current_history_length()

    @classmethod
    def __parseList(cls, token):
        """
        Break up a list token or a filename with possible
        globbing and return a python list for processing
        """
        val = token.value
        list_ = []
        if val.startswith("[") and val.endswith("]"):
            for v in val.lstrip("[").rstrip("]").split(","):
                if v.startswith("'") or v.startswith('"'):
                    list_.append(Token(type_="CNAME",
                                       value=v.strip("'").strip('"')))
                else:
                    list_.append(Token(type_="VARIABLE",
                                       value=v))
        elif "*" in val:  # a file glob
            p = Path('.')
            list_ = [Token(value=l, type_="FILENAME")
                     for l in list(p.glob(val))]
        else:  # just a single file?
            list_ = [Token(value=val, type_="CNAME")]
        return list_

    def run_instruction(self, t):
        """
        Main entry point to the interpreter, takes a tree of
        Tokens from the parser and carries out the instructions
        """
        # print(t)
        args = t.children
        if t.data == 'command':
            # for i, c in enumerate(args):
            # print(str(i)+" arg: "+c+" "+c.type)
            if (args[0].type == 'VARIABLE'):
                self.assignVar(args[0].value, args[2])  # skip =
                return True

            if(len(args) >= 2):  # commands with filename
                res = {
                    'open': self.ogr_open,
                    'save': self.ogr_save,
                    'info': self.ogr_info,
                    'print': self.print_,
                }[args[0]](*args[1:])
            else:
                res = {
                    'list': self.ogr_list,
                    'history': self.history,
                }[args[0]]()
        elif t.data == 'exec':
            res = self.exec_hist(args[1])
        elif t.data == 'repeat_hist':
            res = self.exec_hist("last")
        elif t.data == 'for':
            res = self.__do_for(args)
        elif t.data == 'code_block':
            for cmd in t.children:
                res = self.run_instruction(cmd)
        else:
            raise SyntaxError('Unknown instruction: %s' % t.data)
        return res

    def __do_for(self, arg):
        """
        Process a For token and execute the attached code block
        """
        args = [t for t in arg if not isinstance(t, Token) or
                (isinstance(t, Token) and t.type != 'NEWLINE')]
        variable = args[1]
        list_ = self.__parseList(args[3])
        block = args[4]
        res = False
        for i in list_:
            self.assignVar(variable, i)
            res = self.run_instruction(block)
            if not res:
                break
        return res

    @classmethod
    def history(cls):
        """
        Print out the history file with reference numbers
        """
        length = readline.get_current_history_length()
        for i in range(1, length):
            print("%d: %s" % (i, readline.get_history_item(i)))
        return True

    def exec_hist(self, *args):
        """
        Execute a command from the history. If the user typed '!!' then
        repeat the last command, if '!int' find that command in the list and
        execute it.
        TODO: implement '!prefix'
        """
        if(args[0] == "last"):
            val = readline.get_current_history_length() - 2  # last cmd
        else:
            val = int(args[0].value)
        cmd = readline.get_history_item(val)
        if cmd:
            length = readline.get_current_history_length() - 1
            readline.replace_history_item(length, cmd)
            return self.run(cmd)
        else:
            raise SyntaxError("Unknown history command %s" % val)

    def print_(self, *args):
        """
        Print out the values of a list of tokens - expanding variables if
        present.
        """
        for arg in args:
            if isinstance(arg, Token):
                if (arg.type == 'VARIABLE'):
                    var = arg.value
                    # print("looking up value of "+var)
                    if var in self.vars:
                        resp = self.vars.get(var)
                        if isinstance(resp, Token):
                            print(resp.value)
                        else:
                            print(resp)
                    else:
                        raise SyntaxError('Undefined variable %s' % var)
                else:
                    print(arg.value)
            else:
                print(arg)
        return True

    def __getFileName(self, arg):
        """
        Gets a filename from a token id it is a variable, strips quotes from
        the result. Uses pathlib to resolve name.
        """
        if arg.value in self.vars:
            filename = self.vars.get(arg.value).value
        else:
            filename = arg

        filename = filename.strip('"').strip("'")
        p = Path(filename)
        filename = str(p.resolve())
        return filename

    def ogr_open(self, *args):
        """
        Open a spatial file (with an extension in the drivers dict).
        """
        filename = self.__getFileName(args[0])
        self.dataSource = ogr.Open(filename, 0)
        if self.dataSource is None:
            raise IOError("Could not open %s" % (filename))
        else:
            print('Opened %s' % (filename))
            self.filename = filename
            return True

    def ogr_list(self):
        """
        List the layers in the current datasource
        """
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
        """
        Get information about the named layer in the current datasource, if
        there is another argument then print the full metadata.
        """
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

    def ogr_save(self, fname, lname=None):
        """
        Save the named layer of the current layer in the file
        """
        filename = self.__getFileName(fname)
        idx = filename.rfind(".")
        ext = filename[idx + 1:]
        if lname:
            layername = lname
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
        """
        parse & run the command(s) in the program
        """
        parse_tree = self.parser.parse(program)
        # print(parse_tree.pretty())
        res = False
        for inst in parse_tree.children:
            res = self.run_instruction(inst)
        return res


def main():
    shetland = Interpreter("shetland.g")
    code = ""
    block = False
    cmd = ""
    prompt = "> "
    while True:
        try:
            code = input(prompt)
            if code.strip().endswith("{"):
                # handle code block lines
                block = True
                prompt = "... "
                cmd = code.strip()+"\n"
                continue
            if block:
                cmd += code.strip()+"\n"
                if code.endswith("}"):
                    prompt = "> "
                    try:
                        shetland.run(cmd)
                    except UnexpectedInput as u:
                        print("Unexpected input:\n" +
                              u.get_context(code), u.line, u.column)
            else:
                try:
                    shetland.run(code)
                except UnexpectedInput as u:
                    print("Unexpected input:\n" +
                          u.get_context(code), u.line, u.column)

        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
