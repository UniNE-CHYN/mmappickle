import unittest
import re

class TestModule(unittest.TestCase):
    def test_version_is_canonical(self):
        import mmappickle
        #Regex from PEP-440
        self.assertIsNotNone(re.match(r'^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*((a|b|rc)(0|[1-9]\d*))?(\.post(0|[1-9]\d*))?(\.dev(0|[1-9]\d*))?$', mmappickle.__version__))

if __name__ == '__main__':
    unittest.main()

