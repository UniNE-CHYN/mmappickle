import unittest
import re
import sys

class NumpyFailsToLoadImporter:
    def find_module(self, fullname, path=None):
        if fullname.startswith('numpy.') or fullname == 'numpy':
            return self
        return None

    def load_module(self, fullname):
        raise ImportError(fullname)
    
sys.meta_path.insert(0, NumpyFailsToLoadImporter())


class TestModule(unittest.TestCase):
    def test_import_without_numpy(self):
        #For some reason, this test doesn't work in coverage mode... 
        #(i.e. execution paths are not followed)
        import mmappickle, mmappickle.stubs

if __name__ == '__main__':
    unittest.main()


