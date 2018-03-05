.. internals:

Internals
=========

:class:`mmapdict` files are :mod:`pickle` files, containing a dictionnary, but with a special format. The main idea is to have a file of predictable structure, to be able to compute the offsets for the memory maps. Moreover, there should be a way to disable a specific key, to either replace it or to delete it without changing the offset of the file.

For example, for the following dictionnary:

::

  {'key': 'value', 'test': array([1, 2, 3], dtype=uint8)}


The normal pickle module would output:

::

      0: \x80 PROTO      4
      2: \x95 FRAME      172
     11: }    EMPTY_DICT
     12: \x94 MEMOIZE
     13: (    MARK
     14: \x8c     SHORT_BINUNICODE 'test'
     20: \x94     MEMOIZE
     21: \x8c     SHORT_BINUNICODE 'numpy.core.multiarray'
     44: \x94     MEMOIZE
     45: \x8c     SHORT_BINUNICODE '_reconstruct'
     59: \x94     MEMOIZE
     60: \x93     STACK_GLOBAL
     61: \x94     MEMOIZE
     62: \x8c     SHORT_BINUNICODE 'numpy'
     69: \x94     MEMOIZE
     70: \x8c     SHORT_BINUNICODE 'ndarray'
     79: \x94     MEMOIZE
     80: \x93     STACK_GLOBAL
     81: \x94     MEMOIZE
     82: K        BININT1    0
     84: \x85     TUPLE1
     85: \x94     MEMOIZE
     86: C        SHORT_BINBYTES b'b'
     89: \x94     MEMOIZE
     90: \x87     TUPLE3
     91: \x94     MEMOIZE
     92: R        REDUCE
     93: \x94     MEMOIZE
     94: (        MARK
     95: K            BININT1    1
     97: K            BININT1    3
     99: \x85         TUPLE1
    100: \x94         MEMOIZE
    101: \x8c         SHORT_BINUNICODE 'numpy'
    108: \x94         MEMOIZE
    109: \x8c         SHORT_BINUNICODE 'dtype'
    116: \x94         MEMOIZE
    117: \x93         STACK_GLOBAL
    118: \x94         MEMOIZE
    119: \x8c         SHORT_BINUNICODE 'u1'
    123: \x94         MEMOIZE
    124: K            BININT1    0
    126: K            BININT1    1
    128: \x87         TUPLE3
    129: \x94         MEMOIZE
    130: R            REDUCE
    131: \x94         MEMOIZE
    132: (            MARK
    133: K                BININT1    3
    135: \x8c             SHORT_BINUNICODE '|'
    138: \x94             MEMOIZE
    139: N                NONE
    140: N                NONE
    141: N                NONE
    142: J                BININT     -1
    147: J                BININT     -1
    152: K                BININT1    0
    154: t                TUPLE      (MARK at 132)
    155: \x94         MEMOIZE
    156: b            BUILD
    157: \x89         NEWFALSE
    158: C            SHORT_BINBYTES b'\x01\x02\x03'
    163: \x94         MEMOIZE
    164: t            TUPLE      (MARK at 94)
    165: \x94     MEMOIZE
    166: b        BUILD
    167: \x8c     SHORT_BINUNICODE 'key'
    172: \x94     MEMOIZE
    173: \x8c     SHORT_BINUNICODE 'value'
    180: \x94     MEMOIZE
    181: u        SETITEMS   (MARK at 13)
    182: .    STOP
  highest protocol among opcodes = 4

This works fine, but doesn't allow random access.

Let's look at what a :class:`mmappickle.dict` file looks like, for the same data:

::

      0: \x80 PROTO      4
      2: \x95 FRAME      13
     11: J    BININT     1
     16: 0    POP
     17: J    BININT     2
     22: 0    POP
     23: (    MARK
     24: \x95     FRAME      20
     33: \x8c     SHORT_BINUNICODE 'key'
     38: \x8c     SHORT_BINUNICODE 'value'
     45: J        BININT     1
     50: 0        POP
     51: \x88     NEWTRUE
     52: 0        POP
     53: \x95     FRAME      110
     62: \x8c     SHORT_BINUNICODE 'test'
     68: \x8c     SHORT_BINUNICODE 'numpy.core.fromnumeric'
     92: \x8c     SHORT_BINUNICODE 'reshape'
    101: \x93     STACK_GLOBAL
    102: \x8c     SHORT_BINUNICODE 'numpy.core.multiarray'
    125: \x8c     SHORT_BINUNICODE 'fromstring'
    137: \x93     STACK_GLOBAL
    138: \x8e     BINBYTES8  b'\x01\x02\x03'
    150: \x8c     SHORT_BINUNICODE 'uint8'
    157: \x86     TUPLE2
    158: R        REDUCE
    159: K        BININT1    3
    161: \x85     TUPLE1
    162: \x86     TUPLE2
    163: R        REDUCE
    164: J        BININT     0
    169: 0        POP
    170: \x88     NEWTRUE
    171: 0        POP
    172: \x95     FRAME      2
    181: d        DICT       (MARK at 23)
    182: .    STOP
  highest protocol among opcodes = 4

We can note the following changes:

 *  There are hidden values at the beginning (``version = 1``, ``file revision = 2``)
 *  Each key-value couple is in an individual frame, which contain a hidden int (memo max index), finally a hidden TRUE.
 *  The numpy array is created using ``numpy.core.fromnumeric.reshape(numpy.core.multiarray.from_string(data, dtype), shape)`` instead of the "traditionnal" way

The ``version`` field is used to allow further improvements, and is fixed to 1 at present. 
The file revision is increased each time a key of the dict is changed, to allow caching when there is concurrent access.
Memo max index is used because there may be MEMOIZE/GET/PUT to renumber when pickling values. This is a cache to avoid having to parse all the file.

Finally, the hidden TRUE is a "hack" to allow removing a key. 
In fact, it is not possible to move data when it's memmap'ed. 
To avoid this, the first TRUE is replaced by a POP when deleting the key. To summarize, the stack is working in the following way:


 *  Key exists: ``KEY, VALUE, memo max index, POP, TRUE, POP.`` (reduced as ``KEY, VALUE``)
 *  Key doesn't exist: ``KEY, VALUE, memo max index, POP, POP, POP.`` (disappears when reduced)
 
We can see that the file is composed of three differents parts, which are documented below:

 *  The header (:class:`mmappickle.dict._header`)
 *  Storage of each key-value couple (:class:`mmappickle.dict._kvdata`)
 *  A terminator (:class:`mmappickle.dict._terminator`)
 
Extending ``mmappickle``
************************

To add support for a new memory mapped value type, one should create a new subclass :class:`mmappickle.picklers.base`.

This require some knowledge of Python internal pickle format, but should be straightforward, using the numpy picklers as inspiration. Feel free to open an issue if more details are needed.

Internal API Documentation
**************************

.. autoclass:: mmappickle.dict._header
   :members:
   :member-order: bysource
   :special-members:
   :private-members:
   
.. autoclass:: mmappickle.dict._terminator
   :members:
   :member-order: bysource
   :special-members:
   :private-members:
   
.. autoclass:: mmappickle.dict._kvdata
   :members:
   :member-order: bysource
   :special-members:
   :private-members:


.. automodule:: mmappickle.picklers.base
   :members:
   :member-order: bysource
   :special-members:
   :undoc-members:
   :show-inheritance:


.. automodule:: mmappickle.utils
   :members:
   :member-order: bysource
   :special-members:
   :undoc-members:
   :show-inheritance:
