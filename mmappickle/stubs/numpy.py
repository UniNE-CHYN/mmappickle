import numpy
import io

class EmptyNDArray:
    """This is a stub of an empty :class:`numpy.ndarray`
    
    It can be used to allocate a ndarray in a :class:`mmappickle.mmapdict`,
    without having to allocate the ndarray in the RAM.
    
    :param shape: (tuple of ints) Shape of created array
    :param dtype: (:class:`numpy.dtype`) type of the element of the array
    """
    
    def __init__(self, shape, dtype = numpy.float):
        self._shape = shape
        self._dtype = numpy.dtype(dtype)
        
    @property
    def shape(self):
        """The shape of the ndarray"""
        return self._shape
    
    def tofile(self, f):
        """Write the stub to the file, moving the stream position after the data.
        
        :param f: the file object in which to write the data. The stream position should be set at the correct place."""
        #We only seek to the end position, this is fast.
        f.seek(self._dtype.itemsize * numpy.prod(self._shape), io.SEEK_CUR)
    
    @property
    def dtype(self):
        """The data type of the ndarray"""
        return self._dtype
