import io

def save_file_position(f):
    def save_file_position_wrapper(self, *a, **kw):
        old_position = self._file.tell()
        try:
            return f(self, *a, **kw)
        finally:
            self._file.seek(old_position, io.SEEK_SET)
    return save_file_position_wrapper

def require_writable(f):
    def require_writable_wrapper(self, *a, **kw):
        if not self._file.writable():
            raise io.UnsupportedOperation('not writable')
        
        return f(self, *a, **kw)
    
    return require_writable_wrapper