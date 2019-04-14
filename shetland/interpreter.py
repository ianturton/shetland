import os
from lark import Lark, UnexpectedInput
from osgeo import ogr, gdal


class Interpreter:
    drivers = {
        "shp": "ESRI Shapefile", "gpkg": "GPKG"
    }

    def __init__(self, file="shetland.g"):
        __location__ = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))
        with open(os.path.join(__location__, file)) as f:
            grammar = f.read()

        self.parser = Lark(grammar)
        ogr.UseExceptions()
        gdal.UseExceptions()

    def run_instruction(self, t):
        if t.data == 'command':
            args = t.children
            # print(args)
            if(len(args) >= 2):  # commands with filename
                {
                    'open': self.ogr_open,
                    'save': self.ogr_save,
                    'info': self.ogr_info,
                }[args[0]](*args[1:])
            else:
                {
                    'list': self.ogr_list,
                }[args[0]]()
        elif t.data == 'repeat':
            count, block = t.children
            for i in range(int(count)):
                self.run_instruction(block)
        elif t.data == 'code_block':
            for cmd in t.children:
                self.run_instruction(cmd)
        elif t.data == 'instruction':
            print("Instruction "+t.data)
        else:
            raise SyntaxError('Unknown instruction: %s' % t.data)

    def ogr_open(self, *args):
        filename = args[0].value
        self.dataSource = ogr.Open(filename, 0)
        if self.dataSource is None:
            print('Could not open %s' % (filename))
            raise IOError("Could not open %s" % (filename))
        else:
            print('Opened %s' % (filename))
            self.filename = filename

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
        else:
            print("%s not found" % layername)

    def ogr_save(self, *args):
        filename = args[0].value
        idx = filename.rfind(".")
        ext = filename[idx + 1:]
        if len(args) > 1:
            layername = args[1]
        else:
            layername = filename[:idx]

        # look up driver type based on extension
        driverName = self.drivers.get(ext)
        drv = ogr.GetDriverByName(driverName)
        if os.path.exists(filename):
            drv.DeleteDataSource(filename)

        datasource = drv.CreateDataSource(filename)
        if datasource is not None:
            inlayer = self.dataSource.GetLayerByName(layername)
            datasource.CopyLayer(inlayer, new_name=layername)
            datasource = None  # save!
        else:
            print("unable to save to %s" % filename)

    def run(self, program):
        parse_tree = self.parser.parse(program)
        # print(parse_tree.pretty())
        for inst in parse_tree.children:
            self.run_instruction(inst)
        return True


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
