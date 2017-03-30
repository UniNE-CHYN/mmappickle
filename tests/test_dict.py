import unittest
import tempfile
import pickle
import pickletools
import io

from mmappickle import mmapdict

class TestDictBase(unittest.TestCase):
    def test_creation(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f)
            self.assertTrue(m._header.is_valid())
            
    def test_commit_number(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f)
            self.assertEqual(m._header.commit_number, 0)
            self.assertTrue(m._header.is_valid())
            
            m._header.commit_number = 32
            self.assertEqual(m._header.commit_number, 32)
            self.assertTrue(m._header.is_valid())
            
            m._header.commit_number = 465468
            self.assertEqual(m._header.commit_number, 465468)
            self.assertTrue(m._header.is_valid())
            
    def test_valid_pickle(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f)
            f.seek(0)
            
            d = pickle.load(f)
            self.assertDictEqual(d, {})
            
    def test_destructor(self):
        import weakref
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f)
            m_ref = weakref.ref(m)
            del m
                
        self.assertIsNone(m_ref(), "Reference to object is still valid, something is wrong (using object instance instead of weakref.ref?)")
        
class TestKvdata(unittest.TestCase):
    #Since kvdata is fairly complex, it is tested individually
    
    class DictMock:
        class TerminatorMock:
            def write(self):
                pass
            
        def __init__(self, file):
            self._file = file
            self._terminator = self.TerminatorMock()
    
    def test_cache(self):
        from mmappickle.dict import _kvdata
        with tempfile.TemporaryFile() as f:
            d = self.DictMock(f)
            k = _kvdata(d, 0)
            k.data_length = 34
            self.assertEqual(k.data_length, 34)
            
            k = _kvdata(d, 0) #restart
            k.memomaxidx = 1234
            self.assertEqual(k.memomaxidx, 1234)
            
            k = _kvdata(d, 0) #restart
            k.key = "test"
            self.assertEqual(k.key, "test")
            
            k = _kvdata(d, 0) #restart
            self.assertEqual(k.valid, True)  #should be valid by default
            k.valid = False
            self.assertEqual(k.valid, False)
            k.valid = True
            self.assertEqual(k.valid, True)
            
    def test_1(self):
        from mmappickle.dict import _kvdata
        with tempfile.TemporaryFile() as f:
            d = self.DictMock(f)
            k = _kvdata(d, 0)
            k.key = 'test'
            k.data_length = 10
            k.memomaxidx = 5
            
            self.assertEqual(k.key, 'test')
            self.assertEqual(k.data_length, 10)
            self.assertEqual(k.memomaxidx, 5)
            self.assertEqual(k.valid, True)
            
            k.valid = False
            self.assertEqual(k.key, 'test')
            self.assertEqual(k.data_length, 10)
            self.assertEqual(k.memomaxidx, 5)
            self.assertEqual(k.valid, False)
            
    def test_pickle(self):
        from mmappickle.dict import _kvdata
        with tempfile.TemporaryFile() as f:
            f.write(pickle.PROTO + b'\x04' + pickle.MARK)
            d = self.DictMock(f)
            k = _kvdata(d, 3)
            k.key = 'test'
            f.seek(k.data_offset, io.SEEK_SET)
            f.write(pickle.NEWTRUE)
            k.data_length = 1
            k.memomaxidx = 0
            f.seek(0, io.SEEK_END)
            f.write(pickle.DICT + pickle.STOP)
            
            f.seek(0, io.SEEK_SET)
            self.assertDictEqual(pickle.load(f), {'test': True,})
            
            k.valid = False
            f.seek(0, io.SEEK_SET)
            self.assertDictEqual(pickle.load(f), {})
            
            k.valid = True
            f.seek(0, io.SEEK_SET)
            self.assertDictEqual(pickle.load(f), {'test': True,})
            
            with self.assertRaises(RuntimeError):
                k.data_length = 123
                
            with self.assertRaises(AttributeError):
                k.data_offset = 123
                
            with self.assertRaises(RuntimeError):
                k.key = 'ABC'
                
            with self.assertRaises(AttributeError):
                k.key_length = 123
            
            with self.assertRaises(RuntimeError):
                k.memomaxidx = 123
            
class TestDict(unittest.TestCase):
    def _dump_file(self, f):
        f.seek(0, io.SEEK_SET)
        pickletools.dis(f)        
        
    def test_empty(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f)
            
            f.seek(0)
            d = pickle.load(f)
            self.assertDictEqual(d, {})
            
    def test_store_simple(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f)
            m['test'] = 'abc'
            
            self.assertEqual(m['test'], 'abc')
            d = pickle.load(f)
            self.assertDictEqual(d, {'test': 'abc',})
            
    def test_store_ref(self):
        with tempfile.TemporaryFile() as f:
            obj = "1234"
            obj2 = "machin"
            dict_a = {obj: obj, '3': obj,}
            dict_b = {obj: obj2, obj2: obj2, 2: 4, 4: obj,}
            m = mmapdict(f)
            m['dict_a'] = dict_a
            m['dict_b'] = dict_b
            
            self.assertEqual(m['dict_a'], dict_a)
            self.assertEqual(m['dict_b'], dict_b)
            d = pickle.load(f)
            self.assertDictEqual(d, {'dict_a': dict_a, 'dict_b': dict_b,})
            
            import collections
            od = collections.OrderedDict()
            od['obj'] = obj
            od['obj2'] = obj2
            od[obj] = 3
            m['od'] = od
            
            #This should not fail, but will have no effect
            m['od']['machin'] = 'abc'
            
            self.assertEqual(m['od'], od)
            f.seek(0, io.SEEK_SET)
            d = pickle.load(f)
            
            m['od'] = 'abc'
            
            self.assertEqual(m['od'], 'abc')
            
            f.seek(0, io.SEEK_SET)
            d = pickle.load(f)            
            self.assertEqual(d['od'], 'abc')
            
            #self._dump_file(f)
    
    

if __name__ == '__main__':
    unittest.main()