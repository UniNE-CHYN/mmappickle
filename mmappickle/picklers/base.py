import pickle
import struct
import pickletools
import weakref

from ..utils import * 

class BasePickler:
    """Picklers will be tried in decreasing priority order"""
    priority = 0
    
    def __init__(self, parent_object):
        self._parent_object = weakref.ref(parent_object)
        
    @property
    def _file(self):
        return self._parent_object()._file
    
    @save_file_position
    def is_valid(self, offset, length):
        """
        Return True if object starting at offset in f is valid.
        
        File position is kept.
        """
        return False
    
    def is_picklable(self, obj):
        """
        Return True if object can be pickled with this pickler
        """
        return False
        
    @save_file_position
    def read(self, offset, length):
        """Return the unpickled object read from offset, and the length read. File position is kept."""
        raise NotImplementedError("Should be subclassed")
    
    @save_file_position
    def write(self, obj, offset, memo_start_idx = 0):
        """
        Write the pickled object to the file stream, file position is kept.
        
        Returns a tuple (number of bytes, last memo index)"""
        raise NotImplementedError("Should be subclassed")
    
    def _pickle_load_fix(self, p):
        """Load a pickle object from p, adding the header and the terminator. Returns the object."""
        p = pickle.PROTO + struct.pack('<B',4) + p + pickle.STOP
        return pickle.loads(p)
    
    def _pickle_dump_fix(self, obj, memo_start_idx = 0):
        '''
        Pickle and object and optimize its string by changing MEMOIZE into PUT, removing unused PUT/MEMOIZE,
        fixing GET opcodes, and remove PROTO, FRAME, and STOP opcodes.
        
        Returns the pickle bytes, and the end memo index.
        '''
        p = pickle.dumps(obj, 4)
        oldids = set()
        newids = {}
        opcodes = []
        
        #Trick to avoid instanciating objects (we use the "is" operator)
        put = 'PUT'
        get = 'GET'
        
        ops = list(pickletools.genops(p))
        ops = [(x[0],x[1],x[2],y[2]) for x, y in zip(ops[:-1],ops[1:])]+[(ops[-1][0],ops[-1][1],ops[-1][2],len(p))]
        for opcode, arg, pos, end_pos in ops:
            if opcode.name in ('FRAME', 'STOP'):
                #Ignore these
                pass
            elif opcode.name == 'PROTO':
                #Ignore, but check that it's version 4
                assert arg == 4, "Pickle version should be 4"
            elif 'PUT' in opcode.name:
                oldids.add(arg)
                opcodes.append((put, arg))
            elif opcode.name == 'MEMOIZE':
                idx = len(oldids)
                oldids.add(idx)
                opcodes.append((put, idx))
            elif 'GET' in opcode.name:
                newids[arg] = None
                opcodes.append((get, arg))
            else:
                opcodes.append((pos, end_pos))
        del oldids
        
        out = []
        memo_put_idx = memo_start_idx
        for op, arg in opcodes:
            if op is put:
                if arg not in newids:
                    continue
                newids[arg] = memo_put_idx
                if memo_put_idx < 256:
                    data = pickle.BINPUT + struct.pack('<B', memo_put_idx)
                else:
                    data = pickle.LONG_BINPUT + struct.pack('<I', memo_put_idx)                
                memo_put_idx += 1
            elif op is get:
                memo_get_idx = newids[arg]
                if memo_get_idx < 256:
                    data = pickle.BINGET + struct.pack('<B', memo_get_idx)
                else:
                    data = pickle.LONG_BINGET + struct.pack('<I', memo_get_idx)
            else:
                data = p[op:arg]
                
            out.append(data)
        return b''.join(out), memo_put_idx
    
class GenericPickler(BasePickler):
    @property
    def priority(self):
        return -100
    
    @save_file_position
    def is_valid(self, offset, length):
        return True  #catch all
    
    def is_picklable(self, obj):
        return True  #catch all
        
    @save_file_position
    def read(self, offset, length):
        self._file.seek(offset, io.SEEK_SET)
        return self._pickle_load_fix(self._file.read(length)), length
    
    @save_file_position
    def write(self, obj, offset, memo_start_idx = 0):
        self._file.seek(offset, io.SEEK_SET)
        data, memo_idx = self._pickle_dump_fix(obj, memo_start_idx)
        data_length = self._file.write(data)
        return data_length, memo_idx