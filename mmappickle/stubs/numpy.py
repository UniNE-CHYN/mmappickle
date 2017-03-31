import numpy
import io

class EmptyNDArray:
    def __init__(self, shape, dtype = numpy.float):
        self._shape = shape
        self._dtype = numpy.dtype(dtype)
        
    @property
    def shape(self):
        return self._shape
    
    def tofile(self, f):
        f.seek(self._dtype.itemsize * numpy.prod(self._shape), io.SEEK_CUR)
    
    @property
    def dtype(self):
        return self._dtype