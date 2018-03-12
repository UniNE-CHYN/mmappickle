---
title: 'mmappickle: Python 3 module to store memory-mapped numpy array in pickle format'
tags:
  - memory-mapped
  - mmap
  - memmap
  - numpy array
  - pickle
authors:
 - name: Laurent Fasnacht
   orcid: 0000-0002-9853-8209
   affiliation: 1
affiliations:
 - name: University of Neuchâtel
   index: 1
date: 5 March 2018
bibliography: paper.bib
---

# Summary

Mmappickle is a Python 3 library which enables storing large numpy arrays into a file, along with the associated metadata, and to retrieve it in such a way that the numpy array are memory-mapped (numpy.memmap) instead of copied into the system memory.

This library allows working on matrices bigger than the size of the RAM, and allows concurrent read/write access from multiple processes, while having data stored in a structure behaving like a normal Python dictionary. Moreover, the file complies with the Python Pickle format, and can be loaded on computers which don't have mmappickle installed (provided enough RAM is available to load all the matrices).

Mmappickle is designed to be used for the development of parallel algorithms, using for example the Python [multiprocessing](https://docs.python.org/3/library/multiprocessing.html) module [@pythonmultiprocessing].
 
Alternative solutions exist, for example:
- The various bindings for HDF5, like [pytables](http://www.pytables.org/) [@pytables] or [h5py](https://www.h5py.org/) [@collette_python_hdf5_2014]. However, they have severe limitations for concurrent access, and the API adds complexity to the source code. It also adds additional binary dependencies (and therefore requires either a compiler or binary packages).
- The direct use of [numpy.memmap](https://docs.scipy.org/doc/numpy/reference/generated/numpy.memmap.html) [@numpymemmap]. Unfortunately, [numpy.memmap](https://docs.scipy.org/doc/numpy/reference/generated/numpy.memmap.html) is only able to store the matrix data into a file, but not its shape (i.e. its dimensionality) or datatype. Moreover, [numpy.memmap](https://docs.scipy.org/doc/numpy/reference/generated/numpy.memmap.html) is difficult to use in practice because one needs to work on multiple matrices simultaneously (and even additional metadata) and the direct use of [numpy.memmap](https://docs.scipy.org/doc/numpy/reference/generated/numpy.memmap.html) is particularly challenging in this situation.
- The use of [numpy.lib.format.open_memmap](https://github.com/numpy/numpy/blob/8d5bdd1/numpy/lib/format.py#L696) [@numpyopenmemmap], which is not documented in the numpy main documentation. It is a wrapper to [numpy.memmap](https://docs.scipy.org/doc/numpy/reference/generated/numpy.memmap.html), which uses the standard npy file format (hence storing the shape and the datatype). It still has the limitation that only one array can be stored per file, and it requires specifying an explicit file access mode. This is an inconvenience, because a wrong choice of access mode can result in overwriting the file, resulting in data loss.

Mmappickle exhibits similar performance as these alternative solutions, as the underlying array access technique is similar. Mmappickle is also the only approach capable of handling arrays with masked values (i.e. missing data).

This library is currently used for storing and processing hyperspectral imaging data.

# Limitation and further work

As this library relies on Python Pickle format, which is [not secure](https://docs.python.org/3/library/pickle.html) [@pythonpickle], it should not be used with files from untrusted sources.

Further work is ongoing to allow it to load data directly when needed from a (trusted) HTTP server, in order to simplify data distribution.

# References
