import numpy
import io
import pickle
import struct

from .base import BasePickler
from ..utils import *
from ..stubs.numpy import EmptyNDArray

class ArrayPickler(BasePickler):
    def __init__(self, parent_object):
        super().__init__(parent_object)
        self._header = (
            self._pickle_dump_fix('numpy.core.fromnumeric')[0] +
            self._pickle_dump_fix('reshape')[0] +
            pickle.STACK_GLOBAL +

            self._pickle_dump_fix('numpy.core.multiarray')[0] +
            self._pickle_dump_fix('fromstring')[0] +
            pickle.STACK_GLOBAL
        )
        
    @save_file_position
    def is_valid(self, offset, length):
        self._file.seek(offset, io.SEEK_SET)
        data = self._file.read(len(self._header))
        
        return data == self._header
    
    def is_picklable(self, obj):
        return type(obj) in (numpy.ndarray, numpy.memmap, EmptyNDArray)
    
    @property
    def priority(self):
        return 100
    
    @save_file_position
    def write(self, obj, offset, memo_start_idx = 0):
        if len(str(obj.dtype)) >= 256:
            raise ValueError("dtype length should be less than 256")
        self._file.seek(offset, io.SEEK_SET)
        retlength = 0
        retlength += self._file.write(self._header)
        
        #Write a 64-bits long bytes string
        retlength += self._file.write(pickle.BINBYTES8)
        #skip the (yet) unknown size
        self._file.seek(8, io.SEEK_CUR)
        
        #Write to file
        startpos = self._file.tell()
        obj.tofile(self._file)
        endpos = self._file.tell()
        
        retlength += (endpos - startpos)
        
        #Write length
        self._file.seek(startpos - 8, io.SEEK_SET)
        retlength += self._file.write(struct.pack('<Q', endpos - startpos))
        
        #Continue wrinting
        self._file.seek(endpos, io.SEEK_SET)
        retlength += self._file.write(self._pickle_dump_fix(str(obj.dtype))[0])
        retlength += self._file.write(pickle.TUPLE2+pickle.REDUCE)
        retlength += self._file.write(self._pickle_dump_fix(obj.shape)[0])
        retlength += self._file.write(pickle.TUPLE2+pickle.REDUCE)
        
        self._file.seek(startpos, io.SEEK_SET)
        
        return retlength, 0
    
    @save_file_position
    def read(self, offset, length):
        self._file.seek(offset)
        
        assert self._file.read(len(self._header)) == self._header
        
        datatype = self._file.read(1)
        if datatype == pickle.SHORT_BINBYTES:
            datalength = struct.unpack('<B',self._file.read(1))[0]
        elif datatype == pickle.BINBYTES:
            datalength = struct.unpack('<I',self._file.read(4))[0]
        elif datatype == pickle.BINBYTES8:
            datalength = struct.unpack('<Q',self._file.read(8))[0]
        else:
            raise ValueError("Invalid data type")
            
        datastart = self._file.tell()
        #Move after data
        self._file.seek(datalength, io.SEEK_CUR)
        
        #Then we have the dtype string, which should be short
        assert self._file.read(1) == pickle.SHORT_BINUNICODE
        dtypelength = struct.unpack('<B',self._file.read(1))[0]
        dtype = self._file.read(dtypelength).decode('utf8', 'surrogatepass')
        
        #Skip TUPLE2 and REDUCE, to get to the shape tuple
        self._file.seek(2, io.SEEK_CUR)
        
        shapelist = []
        while True:
            shapeelementtype = self._file.read(1)
            if shapeelementtype == pickle.BININT1:
                shapeelement = struct.unpack('<B',self._file.read(1))[0]
            elif shapeelementtype == pickle.BININT2:
                shapeelement = struct.unpack('<H',self._file.read(2))[0]
            elif shapeelementtype == pickle.BININT:
                shapeelement = struct.unpack('<i',self._file.read(4))[0]
            elif shapeelementtype in (pickle.TUPLE1, pickle.TUPLE2, pickle.TUPLE3, pickle.TUPLE):
                #End of tuple
                break
            elif shapeelementtype == pickle.MARK:
                continue #ignore mark
            else:
                assert False, "Invalid element type: 0x{:02x}".format(ord(shapeelementtype))
            shapelist.append(shapeelement)
            
        #Skip TUPLE2 and REDUCE
        self._file.seek(2, io.SEEK_CUR)
        
        length = self._file.tell() - offset
        
        if self._file.writable():
            return numpy.memmap(self._file, dtype=dtype, mode='r+', shape=tuple(shapelist), offset=datastart), length
        else:
            return numpy.memmap(self._file, dtype=dtype, mode='r', shape=tuple(shapelist), offset=datastart), length
    
class MaskedArrayPickler(BasePickler):
    def __init__(self, parent_object):
        super().__init__(parent_object)
        self._array_pickler = ArrayPickler(parent_object)
        self._header = (
            self._pickle_dump_fix('numpy.ma.core')[0] +
            self._pickle_dump_fix('MaskedArray')[0] +
            pickle.STACK_GLOBAL
        )
        
    @save_file_position
    def is_valid(self, offset, length):
        self._file.seek(offset, io.SEEK_SET)
        data = self._file.read(len(self._header))
        
        return data == self._header
    
    def is_picklable(self, obj):
        return type(obj) in (numpy.ma.core.MaskedArray, )
    
    @property
    def priority(self):
        return 100
    
    @save_file_position
    def write(self, obj, offset, memo_start_idx = 0):
        self._file.seek(offset, io.SEEK_SET)
        retlength = 0
        retlength += self._file.write(self._header)
        retlength += self._array_pickler.write(obj.data, offset + retlength)[0]
        retlength += self._array_pickler.write(obj.mask, offset + retlength)[0]
        self._file.seek(offset + retlength)
        retlength += self._file.write(pickle.TUPLE2+pickle.REDUCE)
        
        return retlength, 0
    
    @save_file_position
    def read(self, offset, length):
        self._file.seek(offset)
    
        assert self._file.read(len(self._header)) == self._header
        data, data_pickle_length = self._array_pickler.read(offset + len(self._header), length - offset + len(self._header))
        mask, mask_pickle_length = self._array_pickler.read(offset + len(self._header) + data_pickle_length, length - offset + len(self._header) + data_pickle_length)
        
        #This works, but is inefficient, since it casts the mask into a ndarray
        #ret = numpy.ma.core.MaskedArray(data, mask)
        
        #FIXME: is it a bad idea?
        ret = numpy.ma.core.MaskedArray(data, False)
        ret._mask = mask
        
        return ret, len(self._header) + data_pickle_length + mask_pickle_length + 2
        