Shetland
========

What is Shetland?
-----------------

Shetland is (or aspires to be) an easy to use ETL domain specific
language that allows untrained users to make use of the power of
`ogr2ogr <https://gdal.org/ogr2ogr.html>`__ without the need to look
up the order of the command line arguments every time.

It is written in Python 3 using the `Lark
parser <https://github.com/lark-parser>`__ and builds on the `python
bindings to OGR <https://gdal.org/python/>`__.

Why would you need that?
------------------------

One day while chatting about ETL strategies with a client, I got to
thinking that while “hackers” like me like using ``bash`` and
`ogr <https://gdal.org/>`__, and other people like pointy clicky
windowy interfaces to handle ETL. There is a serious lack of options for
people in between who just want to have a quick look at some data and
save it as a different format, and who then want to do it all 20 files
in the directory with out having to start QGIS up.

Now, obviously there is `Astun <https://astuntechnology.com/>`__\ ’s
`Loader <https://github.com/AstunTechnology/Loader>`__, but it only
knows about GML and KML and there is a bunch of configuration file
editing to get it working.

As there are (at the time of writing) more than 180
`questions <https://gis.stackexchange.com/questions/tagged/ogr>`__ on
`gis.stackexchange <https://gis.stackexchange.com/>`__ it seemed there
was a need for this. Plus it gives me a chance to practice my Python and
improve my understanding of parsers and grammars.

Why call it Shetland?
---------------------

It turns out that other ETLs have used nearly all the good English words
with ETL in them. Also I’m pretty sure there is an `“out of the
box” <https://www.bbc.co.uk/news/uk-scotland-scotland-politics-45733111>`__
joke in here somewhere.
