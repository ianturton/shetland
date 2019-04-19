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
            | "for" VARIABLE "in" LIST code_block -> for

ATOM        : VARIABLE
            | FILENAME
            | CNAME
            | ("\""|"'")? CNAME ("\""|"'")?
code_block  : "{" NEWLINE* (command|NEWLINE)+ NEWLINE* "}"
LIST        : "[" ATOM ("," ATOM)+  "]" | GLOB
GLOB        : (LETTER|DIGIT|"*"|"/"|".")+ 
VARIABLE    : (LETTER)("_"|LETTER|DIGIT)*
FILENAME    : ("\""|"'")? NAME "." EXTENSION ("\""|"'")? 
EXTENSION   : "shp"|"gpkg"|"geojson"|"json"
NAME        : ["/"|"./"|"../"]? (CNAME ["/"])+

%import common.INT -> INTEGER
%import common.LETTER
%import common.DIGIT
%import common.CNAME
%import common.WS_INLINE
%ignore WS_INLINE
%import common.NEWLINE
%ignore NEWLINE
