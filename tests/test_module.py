import unittest
import re

class TestModule(unittest.TestCase):
    def test_version_is_canonical(self):
        import mmappickle
        #Regex from PEP-440
        self.assertIsNotNone(re.match(r'^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*((a|b|rc)(0|[1-9]\d*))?(\.post(0|[1-9]\d*))?(\.dev(0|[1-9]\d*))?$', mmappickle.__version__))
        
    def test_picklersdiscovery(self):
        from mmappickle.dict import mmapdict
        import tempfile
        from mmappickle.picklers import GenericPickler
        class TestPickler(GenericPickler):
            pass
        
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f)
            self.assertIn(True, [x.__class__.__name__ == 'TestPickler' for x in m._picklers])    

if __name__ == '__main__':
    unittest.main()

