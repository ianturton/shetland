import os
from lark import Lark, UnexpectedInput
from osgeo import ogr, gdal


class Interpreter:
    drivers = {
        "shp": "ESRI Shapefile", "gpkg": "GPKG"
    }
    vars = {}

    def __init__(self, file="shetland.g"):
        __location__ = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))
        with open(os.path.join(__location__, file)) as f:
            grammar = f.read()

        self.parser = Lark(grammar)
        ogr.UseExceptions()
        gdal.UseExceptions()

    def run_instruction(self, t):
        print(t)
        if t.data == 'command':
            args = t.children
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
                }[args[0]](*args[1:])
            else:
                res = {
                    'list': self.ogr_list,
                }[args[0]]()
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

    def getFileName(self, arg):
        if arg.type == 'FILENAME':
            filename = arg.value
        elif arg.type == 'VARIABLE':
            if arg.value in self.vars:
                filename = self.vars.get(arg.value).value
            else:
                raise SyntaxError('Undefined variable "%s"' % arg.value)
        filename = filename.strip('"').strip("'")
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
        except EOFError:
            break


if __name__ == '__main__':
    main()
