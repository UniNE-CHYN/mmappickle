Memmap pickle
=============

This Python 3 module enable to store large structure in a python pickle, 
in such a way that the array can be memory-mapped instead of being copied in memory. This module is licensed under the LGPL3 license.

Currently, the container has to be a dictionnary (`mmappickle.dict`), which keys are strings of less than 256 bytes.

It supports any values, but it is only possible to memory-map numpy arrays and numpy masked arrays.

It also supports concurrent access (i.e. you can pass a `mmappickle.dict` an argument which is called using the `multiprocessing` Python module).

Documentation
=============

Documentation is available at http://mmappickle.readthedocs.io/

Contributing
============

Please post issues and pull requests on github. Alternatively, you can also send your patches by email.
