Welcome to mmappickle's documentation!
======================================

This Python 3 module enable to store large structure in a python :mod:`pickle`, in such a way that the array can be memory-mapped instead of being copied in memory. This module is licensed under the LGPL3 license.

Currently, the container has to be a dictionnary (:class:`mmappickle.mmapdict`), which keys are unicode strings of less than 256 bytes.

It supports any values, but it is only possible to memory map :class:`numpy.ndarray` and :class:`numpy.ma.MaskedArray` at present.

It also supports concurrent access (i.e. you can pass a :class:`mmappickle.mmapdict` as an argument which is called using the :mod:`multiprocessing` Python module).

Getting help
============

Please use `mmappickle issue tracker on GitHub <https://github.com/UniNE-CHYN/mmappickle/issues>`_ to report bugs, and to ask any question.


Documentation contents
======================

.. toctree::
   :maxdepth: 2

   install
   quickstart
   api
   internals
   


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

