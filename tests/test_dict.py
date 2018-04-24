import unittest
import tempfile
import pickle
import pickletools
import io
import numpy
import numpy.testing

from mmappickle import mmapdict
from mmappickle.picklers.base import GenericPickler
from mmappickle.picklers.numpy import ArrayPickler, MaskedArrayPickler
from mmappickle.stubs.numpy import EmptyNDArray

class TestDictBase(unittest.TestCase):
    def test_creation(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [GenericPickler])
            self.assertTrue(m._header.is_valid())
            
    def test_commit_number(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [GenericPickler])
            self.assertEqual(m._header.commit_number, 0)
            self.assertTrue(m._header.is_valid())
            
            m._header.commit_number = 32
            self.assertEqual(m._header.commit_number, 32)
            self.assertTrue(m._header.is_valid())
            
            m._header.commit_number = 465468
            self.assertEqual(m._header.commit_number, 465468)
            self.assertTrue(m._header.is_valid())
            
            with self.assertRaises(TypeError):
                m._header.commit_number = 'a'
            self.assertTrue(m._header.is_valid())
            
    def test_valid_pickle(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [GenericPickler])
            f.seek(0)
            
            d = pickle.load(f)
            self.assertDictEqual(d, {})
            
    def test_destructor(self):
        import weakref
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [GenericPickler])
            m_ref = weakref.ref(m)
            del m
                
        self.assertIsNone(m_ref(), "Reference to object is still valid, something is wrong (using object instance instead of weakref.ref?)")

    def test_nonexistent(self):
        import os
        with tempfile.NamedTemporaryFile() as f:
            os.unlink(f.name)
            with self.assertRaises(FileNotFoundError):
                d = mmapdict(f.name, True, picklers = [GenericPickler])
            #This works and re-create the file
            d = mmapdict(f.name, False, picklers = [GenericPickler])
            
    def test_notafile(self):
        import os
        with self.assertRaises(TypeError):
            d = mmapdict({}, picklers = [GenericPickler])
            
            
    def test_readonly(self):
        with tempfile.NamedTemporaryFile() as f:
            m = mmapdict(f, picklers = [GenericPickler])
            m['test1'] = 234
            self.assertTrue(m.writable)
            
            m2 = mmapdict(f.name, True, picklers = [GenericPickler])
            self.assertFalse(m2.writable)
            with self.assertRaises(io.UnsupportedOperation):
                m2['test1'] = 123            
            with self.assertRaises(io.UnsupportedOperation):
                m2['test2'] = 123
            with self.assertRaises(io.UnsupportedOperation):
                del m2['test1']
                
    def test_convert(self):
        with tempfile.NamedTemporaryFile() as f:
            v = {'abc': 123}
            pickle.dump(v, f)
            f.flush()

            m = mmapdict(f, picklers = [GenericPickler])
            assert dict(m) == v
            
    def test_put_opcodes(self):
        import string, itertools
        d_vals = {}
        for s in itertools.product(string.ascii_letters, string.ascii_letters):
            s = ''.join(s)
            d_vals[s] = s
        
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [GenericPickler])
            for i in range(5):
                m['test-{}'.format(i)] = d_vals
            for i in range(5):
                self.assertDictEqual(m['test-{}'.format(i)], d_vals)
                
            
        
                
    def _test_bad_file(self, d, exc=None):
        with tempfile.NamedTemporaryFile() as f:
            f.write(d)
            f.flush()
            
            if exc is not None:
                with self.assertRaises(exc):
                    m = mmapdict(f.name, picklers = [GenericPickler])
            else:
                m = mmapdict(f.name, picklers = [GenericPickler])
                
    def test_bad_file_header_1(self):
        self._test_bad_file(b'\x80', ValueError)
    def test_bad_file_header_2(self):
        self._test_bad_file(b'\x81\x04', ValueError)
    def test_bad_file_header_3(self):
        self._test_bad_file(b'\x80\x03', ValueError)
    def test_bad_file_header_4(self):
        self._test_bad_file(b'\x80\x04\x00', ValueError)
    def test_bad_file_header_5(self):
        self._test_bad_file(b'\x80\x04\x95', ValueError)
    def test_bad_file_header_6(self):
        self._test_bad_file(b'\x80\x04\x95\x00\x00\x00\x00\x00\x00\x00\x00', ValueError)
    def test_bad_file_header_7(self):
        self._test_bad_file(b'\x80\x04\x95\x0d\x00\x00\x00\x00\x00\x00\x00', ValueError)
    def test_bad_file_header_8(self):
        self._test_bad_file(b'\x80\x04\x95\x0d\x00\x00\x00\x00\x00\x00\x00111110111111111', ValueError)
    def test_bad_file_header_9(self):
        self._test_bad_file(b'\x80\x04\x95\x0d\x00\x00\x00\x00\x00\x00\x00J11111111111111', ValueError)
    def test_bad_file_header_10(self):
        self._test_bad_file(b'\x80\x04\x95\x0d\x00\x00\x00\x00\x00\x00\x00J11110111111111', ValueError)
    def test_bad_file_header_11(self):
        self._test_bad_file(b'\x80\x04\x95\x0d\x00\x00\x00\x00\x00\x00\x00J\x01\x00\x00\x000X\x01\x00\x00\x0001', ValueError)
    def test_bad_file_header_12(self):
        self._test_bad_file(b'\x80\x04\x95\x0d\x00\x00\x00\x00\x00\x00\x00J\x01\x00\x00\x000J\x01\x00\x00\x0011', ValueError)
    def test_bad_file_header_13(self):
        self._test_bad_file(b'\x80\x04\x95\x0d\x00\x00\x00\x00\x00\x00\x00J\x01\x00\x00\x000J\x01\x00\x00\x0001', ValueError)
        
        
    def test_bad_terminator(self):
        valid_header = b'\x80\x04\x95\x0d\x00\x00\x00\x00\x00\x00\x00J\x01\x00\x00\x000J\x01\x00\x00\x000('
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
            with self.assertRaises(ValueError):
                k.data_length = -1            
            self.assertEqual(k.data_length, 34)
            
            k = _kvdata(d, 0) #restart
            k.memomaxidx = 1234
            with self.assertRaises(ValueError):
                k.memomaxidx = -1
            self.assertEqual(k.memomaxidx, 1234)
            
            k = _kvdata(d, 0) #restart
            k.key = "test"
            self.assertEqual(k.key, "test")
            
            k = _kvdata(d, 0) #restart
            with self.assertRaises(TypeError):
                k.valid = 1
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
            with self.assertRaises(ValueError):
                k.data_length = -1            
            k.data_length = 10
            k.memomaxidx = 5
            
            self.assertEqual(k.key, 'test')
            self.assertEqual(k.data_length, 10)
            self.assertEqual(k.memomaxidx, 5)
            self.assertEqual(k.valid, True)
            
            k._write_if_allowed()
            k._write_if_allowed()  
            
            k.valid = False
            self.assertEqual(k.key, 'test')
            self.assertEqual(k.data_length, 10)
            self.assertEqual(k.memomaxidx, 5)
            self.assertEqual(k.valid, False)
            
            k._write_if_allowed()
            k._write_if_allowed()
            
    def test_2(self):
        from mmappickle.dict import _kvdata
        with tempfile.TemporaryFile() as f:
            d = self.DictMock(f)
            k = _kvdata(d, 0)
            k.valid = False
            k.key = 'test'
            with self.assertRaises(ValueError):
                k.data_length = -1            
            k.data_length = 10
            k.memomaxidx = 5
            
            
            self.assertEqual(k.key, 'test')
            self.assertEqual(k.data_length, 10)
            self.assertEqual(k.memomaxidx, 5)
            self.assertEqual(k.valid, False)
            
            k._write_if_allowed()
            k._write_if_allowed()
            
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
        
    def test_notpicklable(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [])
            with self.assertRaises(TypeError):
                m['test'] = 'abc'
                
    def test_notreadable(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [GenericPickler])
            m['test'] = 'abc'
            
            m = mmapdict(f, picklers = [])
            with self.assertRaises(ValueError):
                m['test'] == 'abc'
                
    def test_nonexistentkey(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [GenericPickler])
            with self.assertRaises(KeyError):
                del m['test']
            with self.assertRaises(KeyError):
                m['test']
            
    def test_empty(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [GenericPickler])
            
            f.seek(0)
            d = pickle.load(f)
            self.assertDictEqual(d, {})
            
    def test_store_simple(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [GenericPickler])
            m['test'] = 'abc'
            with self.assertRaises(TypeError):
                m[1] = 'aaa'
            
            self.assertEqual(m['test'], 'abc')
            d = pickle.load(f)
            self.assertDictEqual(d, {'test': 'abc',})
            
    def test_readonly(self):
        with tempfile.NamedTemporaryFile() as f:
            m = mmapdict(f.name, picklers = [GenericPickler])
            m['test'] = 'abc'
            self.assertEqual(m['test'], 'abc')
            
            m2 = mmapdict(f.name, readonly = True, picklers = [GenericPickler])
            self.assertEqual(m2['test'], 'abc')
            
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
            
    def test_delitem(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [GenericPickler])
            m['test'] = 'abc'
            self.assertEqual(m['test'], 'abc')
            
            del m['test']
            with self.assertRaises(KeyError):
                print(m['test'])
                
            #reset
            m = mmapdict(f)
            with self.assertRaises(KeyError):
                print(m['test'])
                
            f.seek(0, io.SEEK_SET)
            d = pickle.load(f)
            self.assertDictEqual(d, {})
            
class TestDictNumpyArray(unittest.TestCase):
    def _dump_file(self, f):
        f.seek(0, io.SEEK_SET)
        pickletools.dis(f)        
    def test_store_simple(self):
        with tempfile.TemporaryFile() as f:
            data = numpy.array([[1, 2, 3], [4, 5, 6]])
            m = mmapdict(f, picklers = [ArrayPickler, GenericPickler])
            m['test'] = data
            self.assertIsInstance(m['test'], numpy.memmap)
            numpy.testing.assert_array_equal(m['test'], data)
            f.seek(0)
            d = pickle.load(f)
            numpy.testing.assert_array_equal(d['test'], data)
            
    def test_store_empty(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [ArrayPickler])
            m['test'] = EmptyNDArray((10, 9), dtype = numpy.float32)
            
            self.assertIsInstance(m['test'], numpy.memmap)
            self.assertEqual(m['test'].shape, (10, 9))
            
    def test_store_dims(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [ArrayPickler])
            for i in range(1, 9):
                m['test{}'.format(i)] = numpy.zeros(tuple([1]*i), dtype = numpy.float32)
            
            for i in range(1, 9):
                self.assertEqual(m['test{}'.format(i)].ndim, i)
            
    def test_store_masked(self):
        with tempfile.TemporaryFile() as f:
            data = numpy.ma.MaskedArray([[1, 2, 3], [4, 5, 6]], [[False, True, False], [True, False, True]])
            m = mmapdict(f, picklers = [MaskedArrayPickler])
            m['test'] = data
            self.assertIsInstance(m['test'].data, numpy.memmap)
            self.assertIsInstance(m['test'].mask, numpy.memmap)
            numpy.testing.assert_array_equal(m['test'], data)
            f.seek(0)
            d = pickle.load(f)
            numpy.testing.assert_array_equal(d['test'], data)
            
    def test_masked_bug(self):
        with tempfile.TemporaryFile() as f:
            data = numpy.random.rand(100)
            data = numpy.ma.masked_invalid(data)
            m = mmapdict(f, picklers = [MaskedArrayPickler])
            m['test'] = data
            self.assertIsInstance(m['test'].data, numpy.memmap)
            self.assertIsInstance(m['test'].mask, numpy.memmap)
            numpy.testing.assert_array_equal(m['test'], data)
            f.seek(0)
            d = pickle.load(f)
            numpy.testing.assert_array_equal(d['test'], data)
            
    def test_masked_empty(self):
        with tempfile.TemporaryFile() as f:
            data = numpy.ma.zeros([2, 3], dtype=numpy.int64)
            m = mmapdict(f, picklers = [MaskedArrayPickler, ArrayPickler, GenericPickler])            
            m['test'] = data           
            self.assertIsInstance(m['test'], numpy.ma.masked_array)
            self.assertIsInstance(m['test'].data, numpy.memmap)
            self.assertIsInstance(m['test'].mask, numpy.memmap)            
            numpy.testing.assert_array_equal(m['test'], data)
            d = pickle.load(f)
            numpy.testing.assert_array_equal(d['test'], data)
            
    def test_readonly(self):
        with tempfile.NamedTemporaryFile() as f:
            m = mmapdict(f, picklers = [ArrayPickler])
            m['test'] = numpy.zeros((1, ), dtype = numpy.float32)
            
            m2 = mmapdict(f.name, True, picklers = [ArrayPickler])
            with self.assertRaises(ValueError):
                m2['test'][0] = 2
                

def _tc_increment(args):
    m, idx = args
    m['value'][0] += 1
    
class TestConcurrent(unittest.TestCase):
    def test_concurrent_1(self):
        with tempfile.NamedTemporaryFile() as f:
            m = mmapdict(f.name)
            m['value'] = numpy.zeros((1, ), numpy.float)
            
            import multiprocessing, itertools
            with multiprocessing.Pool(4) as p:
                p.map(_tc_increment, itertools.product([m], range(4)))
                
            self.assertEqual(m['value'], 4)
            
    def test_concurrent_mmapdict_pickle(self):
        #This is not a real test, but it fixes the converage computation since the previous test in not counted
        with tempfile.NamedTemporaryFile() as f:
            m = mmapdict(f.name)
            
            m2 = pickle.loads(pickle.dumps(m))

class TestVacuum(unittest.TestCase):
    def _dump_file(self, f):
        f.seek(0, io.SEEK_SET)
        pickletools.dis(f)    
    def test_vacuum(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f, picklers = [GenericPickler])
            m['a'] = 1
            m['b'] = 2
            m['c'] = 3
            m['d'] = ' ' * 2 * 1024 * 1024
            m['e'] = 5
            m['f'] = 6
            m['g'] = 7
            m['h'] = 8
            
            f.seek(0, io.SEEK_END)
            fsizebefore = f.tell()
            
            del m['b']
            del m['d']
            del m['f']
            del m['g']
            
            f.seek(0, io.SEEK_SET)
            valid_dict = pickle.load(f)
            
            self.assertDictEqual(dict(m), valid_dict)
            
            f.seek(0, io.SEEK_END)
            fsizeafterdel = f.tell()
            
            self.assertEqual(fsizebefore, fsizeafterdel)
            old_commit_number = m.commit_number
            
            m.vacuum()
            
            f.seek(0, io.SEEK_END)
            fsizeaftervacuum = f.tell()
            
            self.assertNotEqual(fsizebefore, fsizeaftervacuum)
            self.assertNotEqual(old_commit_number, m.commit_number)
            self.assertDictEqual(dict(m), valid_dict)
            
            m.commit_number = 143
            m.vacuum()
            self.assertEqual(143, m.commit_number)
            
            #We have to do something otherwise the vacuum won't do anything
            del m['a']
            m.commit_number = 0
            m.vacuum()
            self.assertNotEqual(0, m.commit_number)
            
class TestConvert(unittest.TestCase):
    def _dump_file(self, f):
        f.seek(0, io.SEEK_SET)
        pickletools.dis(f)    
    def test_convert(self):
        with tempfile.TemporaryFile() as f:
            d = {
                'a': 1,
                'b': (1, 2, 3),
                'c': 'test',
            }
            pickle.dump(d, f)
            
            m = mmapdict(f, picklers = [GenericPickler])
            self.assertDictEqual(dict(m), d)
            
    def test_convert_not_possible(self):
        with tempfile.TemporaryFile() as f:
            d = 'abc'
            pickle.dump(d, f)
            
            with self.assertRaises(ValueError):
                m = mmapdict(f, picklers = [GenericPickler])

            
    def test_broken(self):
        with tempfile.TemporaryFile() as f:
            m = mmapdict(f)
            m['a'] = 1
            #self.assertTrue(m.fsck())
            m['b'] = (1, 2, 3)
            m['c'] = 'test'
            
            f.seek(0, io.SEEK_END)
            original_size = f.tell()            
            original_dict = dict(m)
            
            #self.assertTrue(m.fsck())
            
            f.seek(0, io.SEEK_END)
        
            self.assertDictEqual(original_dict, dict(m))
            self.assertEqual(original_size, f.tell())            
            for i in range(1, 13):
                del m
                
                f.truncate(original_size-i)
                
                m = mmapdict(f)
                m.fsck()
                
                f.seek(0, io.SEEK_END)
                
                self.assertDictEqual(original_dict, dict(m))
                self.assertEqual(original_size, f.tell())
                
            #We loose one key...
            del original_dict['c']
            for i in range(14, 20):
                del m
                
                f.truncate(original_size-i)
                
                m = mmapdict(f)
                m.fsck()
                
                f.seek(0, io.SEEK_END)
                
                self.assertDictEqual(original_dict, dict(m))
                
                
                
            
if __name__ == '__main__':
    unittest.main()
