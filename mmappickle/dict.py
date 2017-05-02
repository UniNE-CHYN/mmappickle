import os
import io, pickle, struct
import warnings
import weakref

from .utils import * 

class _header:
    """The file header consists in the following pickle ops:
    PROTO 4                           (pickle version 4 header)
    FRAME <length>
    BININT <_file_version_number:32> POP
        (version of the pickle dict)
    BININT <_file_commit_number:32> POP
        (commit id of the pickle dict, incremented every time something changes)
    <additional data depending on the _file_version_number>
    MARK (start of the dictionnary)
    """
    _file_version_number = 1
    _frame_length = 13
    _commit_number_position = 18
    
    
    def __init__(self, mmapdict, _real_header_starts_at = 0):
        self._mmapdict = weakref.ref(mmapdict)
        self._real_header_starts_at = _real_header_starts_at
        
        #Check if we have a valid header
        if not self.exists:
            self.write_initial()
        
    @property
    def _file(self):
        return self._mmapdict()._file
        
    @property
    @save_file_position
    def exists(self):
        """This returns True if the file contains at least two bytes"""
        self._file.seek(self._real_header_starts_at, io.SEEK_SET)
        newvalue = self._file.read(2)
        return len(newvalue) == 2
    
    @require_writable
    @save_file_position
    def write_initial(self):
        """Write the initial header to the file"""
        data = pickle.BININT + struct.pack('<i', self._file_version_number) + pickle.POP + \
            pickle.BININT + struct.pack('<i', 0) + pickle.POP + \
            pickle.MARK
        
        header = pickle.PROTO + struct.pack('<B', 4) + pickle.FRAME + struct.pack('<Q', len(data)) + data
        self._file.seek(self._real_header_starts_at, io.SEEK_SET)
        self._file.write(header)
        
        
    @save_file_position
    def is_valid(self):
        self._file.seek(self._real_header_starts_at, io.SEEK_SET)
        if self._file.read(1) != pickle.PROTO:
            warnings.warn("File is not a pickle file")
            return False
        if self._file.read(1) != bytes([4]):
            warnings.warn("File is not a pickle file of version 4")
            return False
        if self._file.read(1) != pickle.FRAME:
            warnings.warn("Pickle doesn't start with a FRAME")
            return False
        
        frame_length = self._file.read(8)
        if len(frame_length) != 8:
            warnings.warn("Unable to read FRAME length")
            return False
        
        frame_length = struct.unpack('<Q', frame_length)[0]
        
        if frame_length != self._frame_length:
            warnings.warn("First FRAME lenght {} is not of correct length (should be {})".format(frame_length, self._frame_length))
            return False
        
        frame_contents = self._file.read(frame_length)
        
        if len(frame_contents) != frame_length:
            warnings.warn("Could not read the first FRAME contents")
            return False
        
        if frame_contents[0] != pickle.BININT[0] or frame_contents[5] != pickle.POP[0]:
            warnings.warn("FRAME doesn't containt BININT <version> POP")
            return False
        file_version_number_read = struct.unpack('<i', frame_contents[1:5])[0]
        if file_version_number_read != self._file_version_number:
            warnings.warn("File has the wrong version number {} (should be {})".format(file_version_number_read, self._file_version_number))
            return False
        
        if frame_contents[6] != pickle.BININT[0] or frame_contents[11] != pickle.POP[0]:
            warnings.warn("FRAME doesn't containt BININT <commit_number> POP")
            return False
        
        if frame_contents[-1] != pickle.MARK[0]:
            warnings.warn("FRAME doesn't end with a MARK")
            return False
        
        return True
    
    @property
    @save_file_position
    def commit_number(self):
        self._file.seek(self._real_header_starts_at + self._commit_number_position, io.SEEK_SET)
        return struct.unpack('<i', self._file.read(4))[0]
    
    
    @commit_number.setter
    @require_writable
    @save_file_position
    def commit_number(self, newvalue):
        if type(newvalue) != int:
            raise TypeError('commit_number should be an int')
        
        self._file.seek(self._real_header_starts_at + self._commit_number_position, io.SEEK_SET)
        self._file.write(struct.pack('<i', newvalue))
        
    def __len__(self):
        #Pickle header, FRAME + frame_length + frame data
        return self._real_header_starts_at + 2 + 9 + self._frame_length
    
class _terminator:
    """Terminator is the following pickle ops:
    FRAME 2
    DICT (make the dictionnary)
    STOP (end of the file)
    """
    _data = pickle.FRAME + struct.pack('<Q', 2) + pickle.DICT + pickle.STOP
    
    def __init__(self, mmapdict):
        self._mmapdict = weakref.ref(mmapdict)
        
        #Check if we have a valid header
        if not self.exists:
            self.write()
        
    def __len__(self):
        return len(self._data)
    
    @property
    def _file(self):
        return self._mmapdict()._file    
        
    @property
    @save_file_position
    def exists(self):
        """This returns True if the file contains at least two bytes"""
        self._file.seek(-len(self._data), io.SEEK_END)
        newvalue = self._file.read(len(self._data))
        return newvalue == self._data
            
    @require_writable
    @save_file_position
    def write(self):
        #Do not write two terminators
        if self.exists:
            return
        
        self._file.seek(0, io.SEEK_END)
        self._file.write(self._data)
        
class _kvdata:
    """kvdata is the structure holding a key-value data entry. It has the following pickle ops:
    FRAME <length>
    SHORT_BINUNICODE <length> <key bytes>
    <<< data >>>
    BININT <max memo idx> POP (max memo index of this part)
    NEWTRUE|POP POP (if NEWTRUE POP: entry is valid, else entry is deactivated.)
    """    
    def __init__(self, mmapdict, offset):
        self._mmapdict = weakref.ref(mmapdict)
        self._offset = offset
        self._exists = self._exists_initial
        #Cache for non-written entries
        self._cache = {
            'valid': True,
            #key, data_length, memomaxidx
        }
        
    def __len__(self):
        return self._frame_length + 9
    
    @property
    def offset(self):
        return self._offset
    
    @property
    def end_offset(self):
        return self._offset + len(self)
    
    @property
    def _file(self):
        return self._mmapdict()._file
    
    @property
    @save_file_position
    def _frame_length(self):
        if not self._exists:
            return 2 + self.key_length + self.data_length + 1 + 4 + 1 + 1 + 1
        self._file.seek(self._offset + 1, io.SEEK_SET)
        return struct.unpack('<Q', self._file.read(8))[0]
        
    @property
    @save_file_position
    def _exists_initial(self):
        """This returns True if the file contains at least two bytes"""
        self._file.seek(self._offset, io.SEEK_SET)
        data = self._file.read(10)
        if len(data) < 10:
            return False
        return data[0] == pickle.FRAME[0] and data[9] == pickle.SHORT_BINUNICODE[0]
    
    @property
    def data_length(self):
        if not self._exists:
            return self._cache['data_length']
        return self._frame_length - 2 - self.key_length - 6 - 2
    
    @property
    def data_offset(self):
        return self._offset + 9 + 2 + self.key_length
        
    @property
    @save_file_position
    def key_length(self):
        if not self._exists:
            return len(self._cache['key'].encode('utf8','surrogatepass'))
        self._file.seek(self._offset + 10)
        return self._file.read(1)[0]
        
    @property
    @save_file_position
    def key(self):    
        if not self._exists:
            return self._cache['key']
        key_length = self.key_length
        self._file.seek(self._offset + 11, io.SEEK_SET)
        return self._file.read(key_length).decode('utf8')
    
    @property
    def _valid_offset(self):
        return self._offset + 9 + self._frame_length - 2
    
    @property
    @save_file_position
    def valid(self):    
        if not self._exists:
            return self._cache['valid']
        self._file.seek(self._valid_offset, io.SEEK_SET)
        return self._file.read(1) == pickle.NEWTRUE
    
    @property
    def _memomaxidx_offset(self):
        return self._offset + 9 + self._frame_length - 7
    
    @property
    @save_file_position
    def memomaxidx(self):    
        if not self._exists:
            return self._cache['memomaxidx']
        self._file.seek(self._memomaxidx_offset, io.SEEK_SET)
        return struct.unpack('<i', self._file.read(4))[0]
    
    @data_length.setter
    def data_length(self, newvalue):
        if self._exists:
            raise RuntimeError("Cannot set data_length of an existing key-value entry")
        if type(newvalue) != int or newvalue < 0:
            raise ValueError("data_length should be a non-negative integer")
        self._cache['data_length'] = newvalue
        self._write_if_allowed()
        
    @key.setter
    def key(self, newvalue):
        if self._exists:
            raise RuntimeError("Cannot set key of an existing key-value entry")
        if type(newvalue) != str:
            raise TypeError("key should be a string")
        self._cache['key'] = newvalue
        self._write_if_allowed()
        
    @memomaxidx.setter
    def memomaxidx(self, newvalue):
        if self._exists:
            raise RuntimeError("Cannot set key of an existing key-value entry")
        if type(newvalue) != int or newvalue < 0:
            raise TypeError("memomaxidx should be a positive int")
        self._cache['memomaxidx'] = newvalue
        self._write_if_allowed()
    
    @valid.setter
    @require_writable
    @save_file_position
    def valid(self, newvalue):
        if type(newvalue) != bool:
            raise TypeError("valid should be a boolean")
        if self._exists:
            self._file.seek(self._valid_offset, io.SEEK_SET)
            if newvalue:
                self._file.write(pickle.NEWTRUE)
            else:
                self._file.write(pickle.POP)
        else:
            self._cache['valid'] = newvalue
            
    @require_writable
    @save_file_position
    def _write_if_allowed(self):
        #Do not write if it already exists
        if self._exists:
            return
        
        if not all(x in self._cache for x in ('valid', 'key', 'data_length', 'memomaxidx')):
            #Not writable yet
            return
        
        
        self._file.seek(self._offset, io.SEEK_SET)
        key = self.key.encode('utf8','surrogatepass')
        self._file.write(pickle.FRAME + struct.pack('<Q',self._frame_length) + \
                         pickle.SHORT_BINUNICODE + struct.pack('<B', len(key)) + key)
        #Skip data
        self._file.seek(self.data_length, io.SEEK_CUR)
        self._file.write(pickle.BININT + struct.pack('<i',self.memomaxidx) + pickle.POP)
        
        if self.valid:
            self._file.write(pickle.NEWTRUE + pickle.POP)
        else:
            self._file.write(pickle.POP + pickle.POP)
        
        #This entry now exists
        self._exists = True
        #Rewrite terminator
        self._mmapdict()._terminator.write()
        
class mmapdict:
    _required_file_methods = ('fileno', 'seek', 'read', 'write', 'writable', 'truncate', 'tell')
    
    def __init__(self, file, readonly = None, picklers = None):
        """
        Create or load a mmap dictionnary.
        
        file is a file-like object or a string representing the name of the file.
        
        When using a file name, the optional readonly argument can be used to specify if the file
        can be written or not.
        """
        
        #Open the file if f is a string.
        if type(file) == str:
            if readonly:
                if os.path.exists(path):
                    self._file = open(file, 'rb')
                else:
                    raise FileNotFoundError("Cannot readonly memmap a non-existent file {!r}".format(file))
            if os.path.exists(file):
                self._file = open(file, 'rb+')
            else:
                self._file = open(file, 'wb+')
        else:
            if not all(hasattr(file, x) for x in mmapdict._required_file_methods):
                raise TypeError('f should be a str, or have a the following methods: {}'.format(', '.join(mmapdict._required_file_methods)))
            self._file = file
            
        self._header = _header(self)
        self._terminator = _terminator(self)
        
        if picklers is None:
            from .picklers.base import BasePickler
            def all_subclasses(cls):
                return cls.__subclasses__() + [g for s in cls.__subclasses__() for g in all_subclasses(s)]
            
            picklers = [x(self) for x in all_subclasses(BasePickler)]
            if len(picklers) == 0:
                from .picklers import GenericPickler
                picklers = [x(self) for x in all_subclasses(BasePickler)]
        else:
            picklers = [x(self) for x in picklers]
        
        self._picklers = list(sorted(picklers, key = lambda x: x.priority, reverse=True))
        
        #Cache/lock infrastructure
        self._locked = 0
        self._cache_commit_number = None
        self._cache_clear()
        
        #Ensure it's a valid file
        if not self._header.is_valid():
            self._convert_file()
            
    def __getstate__(self):
        """ This is called before pickling. """
        state = self.__dict__.copy()
        filename = state['_file'].name
        filemode = state['_file'].mode
        filemode = filemode.replace('w', 'r')  #Do not allow w+ modes (would destroy file)
        state['_file'] = (filename, filemode)
        state['_header'] = None
        state['_terminator'] = None
        state['_locked'] = 0
        state['_cache_commit_number'] = None
        state['_cache_kv'] = None
        state['_cache_kv_all'] = None
        state['_picklers'] = [x.__class__ for x in state['_picklers']]
        
        return state
    
    def __setstate__(self, state):
        """ This is called while unpickling. """
        state['_file'] = open(state['_file'][0], state['_file'][1])
        self.__dict__.update(state)
        
        self._picklers = [x(self) for x in self._picklers]
        
        self._header = _header(self)
        self._terminator = _terminator(self)
        
        
    @property
    def writable(self):
        return self._file.writable()
    
    @property
    @lock
    def commit_number(self):
        return self._header.commit_number
    
    @commit_number.setter
    @lock
    def commit_number(self, newvalue):
        self._header.commit_number = newvalue
        
    def _cache_clear(self):
        self._cache_kv = None
        self._cache_kv_all = None
        
    @property
    @lock
    @save_file_position
    def _kv_all(self):
        if self._cache_kv_all is None:
            self._cache_kv_all = []
            offset = len(self._header)
            self._file.seek(0, io.SEEK_END)
            end_offset = self._file.tell() - len(self._terminator)
            while offset < end_offset:
                this_kv = _kvdata(self, offset)
                self._cache_kv_all.append(this_kv)
                offset += len(this_kv)

        return self._cache_kv_all
    
    @property
    @lock
    @save_file_position
    def _kv(self):
        if self._cache_kv is None:
            self._cache_kv = {}
            for k in self._kv_all:
                if k.valid:
                    self._cache_kv[k.key] = k

        return self._cache_kv
    
    @lock
    def __contains__(self, k):
        return k in self._kv
    
    @lock
    def keys(self):
        return self._kv.keys()
    
    @require_writable
    @lock
    @save_file_position
    def __setitem__(self, k, v):
        if k in self:
            del self[k]
            
        found = False
        for pickler in self._picklers:
            if pickler.is_picklable(v):
                found = True
                break
        
        if not found:
            raise TypeError("Could not find a pickler for element of type {}".format(type(v)))
            
            
        offset = max([x.end_offset for x in self._kv_all] + [len(self._header)])
        memomaxidx = max([x.memomaxidx for x in self._kv_all] + [1])
        kv = _kvdata(self, offset)
        kv.key = k
        kv.data_length, kv.memomaxidx = pickler.write(v, kv.data_offset, memomaxidx)
        #Update cache
        self._cache_kv[kv.key] = kv
        self._cache_kv_all.append(kv)
        self.commit_number += 1
    
    @lock
    def __getitem__(self, k):
        if k not in self:
            raise KeyError(k)
            
        data_offset = self._kv[k].data_offset
        data_length = self._kv[k].data_length
        found = False
        for pickler in self._picklers:
            if pickler.is_valid(data_offset, data_length):
                found = True
                break
            
        if not found:
            raise ValueError("No picklers are valid to key {!r}".format(k))
        return pickler.read(data_offset, data_length)[0]
        
    @require_writable
    @lock
    @save_file_position
    def __delitem__(self, k):
        if k not in self:
            raise KeyError(k)
        
        self._kv[k].valid = False
        del self._kv[k]
        self.commit_number += 1
        
    @require_writable
    @lock
    @save_file_position
    def vacuum(self, chunk_size = 1048576):
        """
        Free all deleted keys.
        
        CAUTION: NO MMAP SHOULD EXIST ON FILE! (data will be shifted).
        """
        holes = []
        for kv in self._kv_all:
            assert isinstance(kv, _kvdata)
            if kv.valid:
                continue
            
            holes.append((kv.offset, kv.end_offset))

        self._file.seek(0, io.SEEK_END)
        file_size = self._file.tell()
        #Reverse to get data ranges instead of holes
        data_ranges = []
        data_ranges = list(zip([0] + [h[1] for h in holes], [h[0] for h in holes] + [file_size]))
        data_ranges = [d for d in data_ranges if d[0] != d[1]]
        
        if len(data_ranges) == 1:
            return  #Nothing to do...
        
        wptr = 0
        for data_range in data_ranges:
            rptr = data_range[0]
            
            while rptr < data_range[1]:
                self._file.seek(rptr, io.SEEK_SET)
                data = self._file.read(min(data_range[1] - rptr, chunk_size))
                rptr += len(data)
                
                self._file.seek(wptr, io.SEEK_SET)
                wptr += self._file.write(data)
                
        self._file.seek(wptr, io.SEEK_SET)
        self._file.truncate()
        
        self._cache_clear()
        #Set the commit number to zero, except if it was already 0 (always change it)
        if self.commit_number == 0:
            self.commit_number = 1
        else:
            self.commit_number = 0

    @require_writable
    def _convert_file(self, chunk_size = 1048576):
        warnings.warn("Converting to new format... this may require a LOT of memory...")
        
        self._file.seek(0)
        data = pickle.load(self._file)
        
        if type(data) != dict:
            raise ValueError("Could not load a pickle which is not a dictionnary")
        
        end_of_pickle = self._file.tell()
        
        #Now, write a header at the end of the pickle
        #This has the advantage of not destroying the file if it fails due to not enough memory
        self._file.truncate()
        self._header = _header(self, _real_header_starts_at=end_of_pickle)
        
        #Write all data in the new format
        for k in data.keys():
            self[k] = data[k]
            
        #Move data to the beginning of the file (this is where a failure may be bad ;-)
        self._file.seek(0, io.SEEK_END)
        data_length = self._file.tell() - end_of_pickle
        
        wptr = 0
        rptr = end_of_pickle
        while wptr < data_length:
            self._file.seek(rptr, io.SEEK_SET)
            data = self._file.read(min(chunk_size, data_length - wptr))
            rptr += len(data)
            self._file.seek(wptr)
            wptr += self._file.write(data)
            
        assert wptr == data_length
        self._file.seek(wptr)
        self._file.truncate()
        
        self._header = _header(self)
        self._cache_clear()
        self.vacuum(chunk_size)  #Normally not needed, but should not harm
        
    @require_writable
    def fsck(self):
        self._file.seek(0, io.SEEK_END)
        end_offset = self._file.tell()
        
        self._file.seek(2, io.SEEK_SET)
        frame_id = 0
        while True:
            frame_start = self._file.tell()
            frame_id += 1
            
            print("Frame (?) {} starting at {}".format(frame_id, frame_start))
            
            data = self._file.read(9)
            if data[0] != pickle.FRAME[0]:
                raise ValueError("Not on frame boundary")
            frame_length = struct.unpack('<Q', data[1:9])[0]
            if frame_start + 10 + frame_length > end_offset:
                print("Incomplete frame starting at {}".format(frame_start))
                break
            
            if frame_id == 1:
                print("[header]")
                self._file.seek(frame_start + frame_length + 9, io.SEEK_SET)
                continue
            
            first_data = self._file.read(1)
            
            if first_data == pickle.DICT:
                print("[terminator]")
                self._file.seek(frame_start + frame_length + 9 - 1, io.SEEK_SET)
                terminator = self._file.read(1)
                if terminator != pickle.STOP:
                    raise ValueError("Pickle doesn't end with stop!")
                break
            
            if first_data != pickle.SHORT_BINUNICODE:
                print("Frame starts with {}".format(first_data))
                break
            
            key_length = self._file.read(1)[0]
                
            print("Frame [{}]".format(self._file.read(key_length).decode('utf8')))
            self._file.seek(frame_start + frame_length + 9, io.SEEK_SET)
            
        self._file.truncate()
        self._terminator.write()
        

if __name__ == '__main__':
    import sys
    from .picklers import *
    if len(sys.argv) != 2:
        print("If run directly, this script requires exactly one argument, and converts it to the latest mmapdict format.")
        sys.exit(1)
    
    m = mmapdict(sys.argv[1])
