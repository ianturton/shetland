!start: command+

!command: "list"
       | "save" FILENAME [CNAME]
       | "open" FILENAME
       | "info" CNAME

FILENAME    : NAME "." EXTENSION
EXTENSION   : "shp"|"gpkg"
NAME        : ["/"|"."]* (CNAME ["/"])+

%import common.CNAME
%import common.WS
%ignore WS
