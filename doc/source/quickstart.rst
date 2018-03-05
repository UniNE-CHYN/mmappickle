.. _quickstart:

Quick start
===========

:class:`mmappickle.mmapdict` behave exactly like dictionaries. For example:

::

    >>> from mmappickle import mmapdict
    >>> m = mmapdict('/tmp/test.mmdpickle') #could be an existing file
    >>> m['a_sample_key'] = 'value'
    >>> m['other_key'] = [1,2,3]
    >>> print(m['a_sample_key'])
    value
    >>> m['other_key'][2]
    3
    >>> del m['a_sample_key']
    >>> print(m.keys())
    ['other_key']
    
The contents of the dictionary are stored to disk. For example, in another python interpreter:

::

    >>> from mmappickle import mmapdict
    >>> m = mmapdict('/tmp/test.mmdpickle')
    >>> print(m['other_key'])
    [1, 2, 3]
    

It is also possible to open the file read-only, in which case any modification will fail:

::

    >>> from mmappickle import mmapdict
    >>> m = mmapdict('/tmp/test.mmdpickle', True)
    >>> m['other_key'] = 'a'
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/laurent/git/mmappickle/mmappickle/utils.py", line 22, in require_writable_wrapper
        raise io.UnsupportedOperation('not writable')
    io.UnsupportedOperation: not writable

    
Of course, the main interest is to store numpy arrays:

::

    >>> import numpy as np
    >>> from mmappickle.dict import mmapdict
    >>> m = mmapdict('/tmp/test.mmdpickle')
    >>> m['test'] = np.array([1,2,3],dtype=np.uint8)
    >>> m['test'][1] = 4
    >>> print(m['test'])
    [1 4 3]
    >>> print(type(m['test']))
    <class 'numpy.core.memmap.memmap'>
    
As you can see, the ``m['test']`` is now memory-mapped. This means that its content is not loaded in memory, but instead accessed directly from the file.

Unfortunately, the array has to exist in order to serialize it to the ``mmapdict``. If the array exceed the available memory, this won't work. Instead one should use stubs:

::

    >>> from mmappickle.stubs import EmptyNDArray
    >>> m['test_large']=EmptyNDArray((300,300,300))
    >>> print(type(m['test_large']))
    <class 'numpy.core.memmap.memmap'>

The matrix in ``m['test_large']`` uses 216M of memory, but it was at no point allocated in RAM. This way, it is possible to allocate array larger than the size of the memory. One could have written ``m['test_large'] = np.empty((300,300,300))``, but unfortunately the memory is allocated when calling :func:`numpy.empty`.

Finally, one last useful trick is the :meth:`mmappickle.mmapdict.vacuum` method. It allows reclaiming the disk space:

::

    >>> del m['test_large']
    >>> #Here, /tmp/test.mmdpickle still occupies ~216M of hard disk
    >>> m.vacuum()
    >>> #Now the disk space has been reclaimed.
    
.. warning ::

    When running :meth:`mmappickle.mmapdict.vacuum`, it is crucial that there is no other references to the file content, either in this process or in other.
    In particular, no memory-mapped array. If this rule is not followed, the result will be very bad! (crash, data corruption, etc.)
