!start: command+

!command: "list"
       | "save" (FILENAME|VARIABLE) [(CNAME | VARIABLE)]
       | (VARIABLE "=" FILENAME)
       | (VARIABLE "=")? "open" (FILENAME|VARIABLE)
       | "info" (CNAME|VARIABLE)

VARIABLE    : (LETTER)("_"|LETTER)*
FILENAME    : ("\""|"'") NAME "." EXTENSION ("\""|"'") 
EXTENSION   : "shp"|"gpkg"
NAME        : ["/"|"."]* (CNAME ["/"])+

%import common.LETTER
%import common.CNAME
%import common.WS
%ignore WS
