import io
import fcntl
from functools import wraps

def save_file_position(f):
    """Decorator to save the object._file stream position before calling the method"""
    @wraps(f)
    def save_file_position_wrapper(self, *a, **kw):
        old_position = self._file.tell()
        try:
            return f(self, *a, **kw)
        finally:
            self._file.seek(old_position, io.SEEK_SET)
            
    return save_file_position_wrapper

def require_writable(f):
    """Require the object's _file to be writable, otherwise raise an error."""
    @wraps(f)
    def require_writable_wrapper(self, *a, **kw):
        if not self._file.writable():
            raise io.UnsupportedOperation('not writable')
        
        return f(self, *a, **kw)
    
    return require_writable_wrapper

def lock(f):
    """Lock the file during the execution of this method. This is a re-entrant lock."""
    @wraps(f)
    def lock_wrapper(self, *a, **kw):
        self._locked += 1
        
        if self._locked == 1:
            try:
                fcntl.flock(self._file, fcntl.LOCK_EX)
                lock_failed = False
            except OSError:
                #Cannot lock?
                lock_failed = True
            except ValueError:
                #Cannot lock? not a valid file descriptor
                lock_failed = True
                
            if self._cache_commit_number != self.commit_number:
                self._cache_clear()
                self._cache_commit_number = self.commit_number

            if lock_failed:
                self._locked = 0
                
        try:
            return f(self, *a, **kw)
        finally:
            if self._locked == 1:
                if self.commit_number != self._cache_commit_number:
                    self._cache_commit_number = self.commit_number
                    self._file.flush()
                fcntl.flock(self._file, fcntl.LOCK_UN)
            self._locked -= 1
    
    return lock_wrapper
