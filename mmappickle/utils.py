import io
from functools import wraps


def _lock_file(f, exclusive):
    import os
    if os.name == 'nt':
        import win32con
        import win32file
        import pywintypes
        __overlapped = pywintypes.OVERLAPPED()
        hfile = win32file._get_osfhandle(f.fileno())
        dwFlags = win32con.LOCKFILE_EXCLUSIVE_LOCK if exclusive else 0
        win32file.LockFileEx(hfile, dwFlags, 0, -0x10000, __overlapped)
    elif os.name == 'posix':
        import fcntl
        op = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        fcntl.flock(f, op)
    else:
        raise OSError("Unsupported OS")


def _unlock_file(f):
    import os
    if os.name == 'nt':
        import win32con
        import win32file
        import pywintypes
        __overlapped = pywintypes.OVERLAPPED()
        hfile = win32file._get_osfhandle(f.fileno())
        win32file.UnlockFileEx(hfile, 0, -0x10000, __overlapped)
    elif os.name == 'posix':
        import fcntl
        fcntl.flock(f, fcntl.LOCK_UN)
    else:
        raise OSError("Unsupported OS")


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
    """Require the object's _file to be writable, otherwise raise an exception."""
    @wraps(f)
    def require_writable_wrapper(self, *a, **kw):
        if not self._file.writable():
            raise io.UnsupportedOperation('not writable')

        return f(self, *a, **kw)

    return require_writable_wrapper


def lock(write=False):
    """
    Lock the file during the execution of this method. This is a re-entrant lock.

    :param write: If True, uses an exclusive lock for write access to the file. If False, a shared lock is used that enables simultaneous access from multiple processes.
    :return: The actual decorator function.
    """
    def decorator(f):
        @wraps(f)
        def lock_wrapper(self, *a, **kw):
            self._locked += 1

            if self._locked == 1:
                try:
                    _lock_file(self._file, write)
                    lock_failed = False
                except OSError:
                    # Cannot lock?
                    lock_failed = True
                except ValueError:
                    # Cannot lock? not a valid file descriptor
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
                    _unlock_file(self._file)
                self._locked -= 1

        return lock_wrapper
    return decorator
