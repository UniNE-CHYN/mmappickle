import requests
import io

from .dict import mmapdict
from mmappickle.picklers.base import GenericPickler

class http_file_wrapper:
    def __init__(self, url, cache_size, block_size=1048576):
        self._url = url
        self._cache_size = cache_size
        self._cache = {}
        self._block_size = block_size
        self._position = 0
        self._download_count = 0
        
        info = requests.head(url)
        if info.status_code != 200:
            raise FileNotFoundError("Could not open url {} (status code: {})".format(url, info.status_code))
        
        if 'Content-Length' not in info.headers:
            raise io.UnsupportedOperation("Server doesn't give us the length for {}".format(url))
            
        self._size = int(info.headers['Content-Length'])
        
        if info.headers.get('Accept-Ranges', 'none') != 'bytes':
            #Server doesn't support partial download, so download everything at once...
            self._cache[0, self._size] = requests.get(url, stream=True).raw.read()
        
    def seek(self, offset, whence=io.SEEK_CUR):
        if type(offset) != int:
            raise TypeError("offset should be an integer {!r}".format(offset))
        if whence == io.SEEK_SET:
            self._position = offset
        elif whence == io.SEEK_END:
            self._position = self._size + offset
        elif whence == io.SEEK_CUR:
            self._position += offset
        else:
            raise ValueError("Invalid whence (should be between 0 and 2)")
            
        #Clip position to the bounds
        self._position = min(max(0, self._position), self._size)
        return self._position
    
    def _round_to_block(self, v, up=False):
        mod = v % self._block_size
        if mod == 0:
            return v
        
        if up:
            return min(self._size, v + (self._block_size - mod))
        else:
            return v - mod
        
    
    def _download(self, range_from, range_to):
        download_range_from = self._round_to_block(range_from, up=False)
        download_range_to = self._round_to_block(range_to, up=True)
        
        print(download_range_from, download_range_to, self._download_count)
        
        r = requests.get(self._url, headers={"Range": "bytes={}-{}".format(download_range_from, download_range_to-1)}, stream=True)
        self._cache[download_range_from, download_range_to] = r.raw.read()
        self._download_count += 1
        assert len(self._cache[download_range_from, download_range_to]) == download_range_to - download_range_from
        return self._cache[download_range_from, download_range_to][range_from - download_range_from:range_to - download_range_from]
    
    def read(self, length):
        read_range_start = self._position
        read_range_end = min(self._position+length, self._size)
        
        #keys_to_use = list(sorted([k for k in self._cache.keys() if k[0] <= read_range_start and k[1] > read_range_start and k[0] <= read_range_end and k[1] > read_range_end]))
        keys = list(sorted(self._cache.keys()))
        ret = []
        while self._position < read_range_end:
            #Remove keys before position
            while len(keys) > 0 and keys[0][1] <= self._position:
                keys.pop(0)
                
            if len(keys) == 0:
                #No remaining keys, download everything in our range
                data = self._download(self._position, read_range_end)
            elif keys[0][0] > self._position:
                #We have something to download till the next block
                data = self._download(self._position, min(keys[0][0], read_range_end))
            else:
                assert keys[0][0] <= self._position and keys[0][1] > self._position
                part_start = self._position - keys[0][0]
                part_end = read_range_end - keys[0][0]
                data = self._cache[keys[0]][part_start:part_end]
                
            self._position += len(data)
            ret.append(data)
            
        return b''.join(ret)
        
    def fileno(self):
        return -1
    
    def writable(self):
        return False
    
    def tell(self):
        return self._position
    
    def truncate(self, pos):
        raise io.UnsupportedOperation("File not open for writing")
    
    def write(self, b):
        raise io.UnsupportedOperation("File not open for writing")
    

        
    #'read',

def httpdict(url, cache_size=None):
    return mmapdict(http_file_wrapper(url, cache_size), readonly=True, picklers=[GenericPickler])
