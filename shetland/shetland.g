!start      : command+

!command    : "list"
            | "save" ATOM [ATOM]
            | (VARIABLE "=" ATOM )
            | (VARIABLE "=")? "open" ATOM
            | (VARIABLE "=")? "layer" ATOM
            | "info" ATOM
            | "print" VARIABLE
            | "history"
            | "!" INTEGER -> exec

ATOM        : VARIABLE
            | FILENAME
            | CNAME

VARIABLE    : (LETTER)("_"|LETTER|DIGIT)*
FILENAME    : ("\""|"'")? NAME "." EXTENSION ("\""|"'")? 
EXTENSION   : "shp"|"gpkg"|"geojson"|"json"
NAME        : ["/"|"./"|"../"]? (CNAME ["/"])+

%import common.INT -> INTEGER
%import common.LETTER
%import common.DIGIT
%import common.CNAME
%import common.WS
%ignore WS
