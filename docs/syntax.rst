***************
Shetland Syntax
***************

File Handling
=============

+ ``open filename|variable``: Open the named file, or the file name the variable
  contains. This file will become the **current** file for subsequent
  operations.
+ ``save filename|variable [layername]``: save the current datasource in using the
  filename argument's extension to determine the format. If a layername is
  provided just that layer will be saved, otherwise the basename of the filename
  will be used to find a matching layer, this makes single layer files like
  shapefiles work as expected.

Examining Data
==============

+ ``list``: List the layers in the current datasource
+ ``info layer [full]``: display metadata on layer of current datasource

Variables and Loops
===================

+ ``var = expression``: set variable var to expression, expression can be a
  filename or other string
+ ``for var in [list]|glob {code block}``:for each value in the list or each
  file that matches the `glob expression <https://docs.python.org/3/library/pathlib.html#module-pathlib>`_ execute the code block. For example:

.. code-block:: python

  for i in **/*.shp {
    print i  
  }

will list all the shapefiles that are found in directories below this one.

+ ``print expression``: prints the expression to standard out.

Interactive Interpreter
=======================

When run interactively Shetland provides the user with a command line editor,
with full arrow key support (on most operating systems). If arrows are not
supported then use crtl-p for up and crtl-n for down. Crtl-R can be used to
search in the history. Use crtl-c to exit the program.

History Managment
-----------------

Shetland provides a 1000 line history of your command line.

+ ``history``: Print out your history including reference numbers.
+ ``!!``: repeat the last command
+ ``!number``: repeat the command at line number in the history.
