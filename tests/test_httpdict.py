import unittest
import pickle
import numpy
import numpy.testing
import requests

from mmappickle import httpdict
from mmappickle.picklers.base import GenericPickler
from mmappickle.picklers.numpy import ArrayPickler, MaskedArrayPickler
from mmappickle.stubs.numpy import EmptyNDArray

class TestHttpDict(unittest.TestCase):
    def test_load(self):
        url = "http://130.125.10.27:1081/20171024_IlluminationTests/StabilityTest.scan"
        
        dict_httpdict = httpdict(url)
        dict_unpickled = pickle.load(requests.get(url, stream=True).raw)
        
        self.assertSetEqual(set(dict_httpdict.keys()), set(dict_unpickled.keys()))
        for k in dict_unpickled.keys():
            if isinstance(dict_unpickled[k], numpy.ndarray):
                numpy.testing.assert_equal(dict_unpickled[k], dict_httpdict[k])
            else:
                self.assertEqual(dict_unpickled[k], dict_httpdict[k])
        
        

if __name__ == '__main__':
    unittest.main()
