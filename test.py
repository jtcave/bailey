import unittest
import tempfile
import bailey
from bailey.backing import open_store
import bailey.backing.interface
import bailey.client
import bailey.server
import bailey.loader
import os.path
import threading
import xmlrpc.client
from time import sleep
import importlib

class Thing:   
    def __init__(self, *args, **kwds):
        self.args = args
        self.kwds = kwds
    def count_args(self):
        return len(self.args) + len(self.kwds)
    def __eq__(self, other):
        return self.args == other.args and self.kwds == other.kwds

TEST_MODULE_SRC = """
def greeting():
  return "Hellorld!"
"""

class BackingTests(unittest.TestCase):    
    def setUp(self) -> None:
        self.dbRootObj = tempfile.TemporaryDirectory()
        self.dbRoot = self.dbRootObj.name
        self.store = open_store(self.dbRoot)
    def tearDown(self) -> None:
        self.dbRootObj.cleanup()

    def test_simple_crud(self):
        store = self.store
        key = "/answer"
        value = 42
        
        self.assertNotIn(key, store)
        
        store[key] = value
        self.assertIn(key, store)
        self.assertEqual(value, store[key]) 

        value2 = value + 2
        store[key] = value2
        self.assertIn(key, store)
        self.assertEqual(value2, store[key]) 

        del store[key]
        self.assertNotIn(key, store)
        
    
    def test_crud_collections(self):
        store = self.store
        key1 = "/my_tuple"
        key2 = "/my_dict"

        val2 = {'spam': 1, 'eggs': 42}
        val1 = tuple(val2.keys())

        self.assertNotIn(key1, store)
        self.assertNotIn(key2, store)

        store[key1] = val1
        store[key2] = val2
        self.assertIn(key1, store)
        self.assertEqual(val1, store[key1])
        self.assertIn(key2, store)
        self.assertEqual(val2, store[key2])

        del store[key1]
        del store[key2]
        self.assertNotIn(key1, store)
        self.assertNotIn(key2, store)

    
    def test_crud_customclass(self):
        key = "/custom_thing"
        val = Thing('spam', 'eggs', 7, likes_spam=False, guest='viking')
        store = self.store

        self.assertNotIn(key, store)
        store[key] = val
        self.assertIn(key, store)
        ret: Thing = store[key]
        self.assertEqual(val.count_args(), ret.count_args())
        self.assertEqual(val, ret)

        del store[key]
        self.assertNotIn(key, store)


    def test_complex_paths(self):
        # list of tuples for deterministic order
        items = [
            ('/easy', 0),
            ('/spam/eggs', 1),
            ('/eggs/bacon/spam/eggs', 2),
            ('/spam and eggs/beans_on_toast', 3),
            ('/zh/汉语', 5),
            ('forgot a slash', "but that's ok")
        ]

        store = self.store
        for k,v in items:
            self.assertNotIn(k, store)
            store[k] = v
        for k,v in items:
            self.assertIn(k, store)
            ret = store[k]
            self.assertEqual(v, ret)
        for k,_ in items:
            del store[k]
            self.assertNotIn(k, store)
    

    def test_enumeration(self):
        items = {
            '/spam': 1,
            '/eggs': 2,
            '/ham': 3,
            '/depth/charge': True
        }
        store = self.store

        for k,v in items.items():
            self.assertNotIn(k, store)
            store[k] = v
            self.assertIn(k, store)
        
        self.assertTrue(all(k in store for k in store))
        items_keyset = items.keys()
        self.assertTrue(all(k in store for k in items_keyset))
        store_keyset = set(iter(store))
        self.assertTrue(all(k in store for k in store_keyset))
        
    
    def test_disallowed_paths(self):
        from bailey.backing.interface import INVALID_CHARS, INVALID_NAMES
        store = self.store

        for c in bailey.backing.interface.INVALID_CHARS:
            def _thunk(): store[c] = 4
            self.assertRaises(bailey.backing.interface.InvalidKeyException, _thunk)
        
        # TODO: extensions for reserved names ("NUL.txt")
        for n in bailey.backing.interface.INVALID_NAMES:
            def _thunk(): store[n] = 4
            self.assertRaises(bailey.backing.interface.InvalidKeyException, _thunk)
            
    
    def test_superkey_crud(self):
        items = {
            '/food/spam': 1,
            '/food/eggs': 2,
            '/food/ham': 3,
            '/food/cheese': False
        }
        superkey = "/food"
        store = self.store

        self.assertNotIn(superkey, store)
        for k,v in items.items():
            store[k] = v
        self.assertIn(superkey, store)
        
        subkeys = store[superkey]
        keys = [os.path.join('/', superkey, k) for k in subkeys]
        self.assertTrue(all(k in store for k in keys))

def client_server_setup(cls):
    # spin up a server in a background thread
    cls.dbRootObj = tempfile.TemporaryDirectory()
    dbRoot = cls.dbRoot = cls.dbRootObj.name
    def server_thread_func():
        bailey.server.start_server(dbRoot, logRequests=False)
    cls.serverThread = threading.Thread(target=server_thread_func, daemon=True)
    cls.serverThread.start()
    # make the client
    cls.store = bailey.bailey("http://localhost:8080")
    # wait a moment, and if the server keeled over already, abort the test suite
    sleep(0.1)
    if not cls.serverThread.is_alive():
        raise RuntimeError("server thread has ceased")

def client_server_teardown(cls):
    # TODO: force the server to shut down somehow so this can be reused in multiple test cases
    cls.dbRootObj.cleanup()

class ClientServerTests(BackingTests):
    @classmethod
    def setUpClass(cls) -> None:
        client_server_setup(cls)

    @classmethod
    def tearDownClass(cls) -> None:
        client_server_teardown(cls)
    
    def setUp(self) -> None:
        pass
    def tearDown(self) -> None:
        pass

    
    def test_reflection(self):
        self.assertTrue(self.serverThread.is_alive())
        expected_methods = ['get', 'put', 'delete', 'present', 'info']
        observed_methods = self.store.backing.proxy.system.listMethods()
        self.assertTrue(all(m in observed_methods for m in expected_methods))
    
    def test_singleton(self):
        ba1 = bailey.bailey()
        ba2 = bailey.bailey()
        self.assertIs(self.store, ba1)
        self.assertIs(self.store, ba2)

    # override
    def test_disallowed_paths(self):
        for c in bailey.backing.interface.INVALID_CHARS:
            def _thunk(): self.store[c] = 4
            self.assertRaises(xmlrpc.client.Fault, _thunk)
        
        # TODO: extensions for reserved names ("NUL.txt")
        for n in bailey.backing.interface.INVALID_NAMES:
            def _thunk(): self.store[n] = 4
            self.assertRaises(xmlrpc.client.Fault, _thunk)
    
    # override
    @unittest.expectedFailure
    def test_enumeration(self):
        self.fail("remote enumeration isn't properly supported yet")
    
    def test_import_machinery(self):
        bailey.loader.install_loader()
        bailey.bailey()['/py/hello'] = TEST_MODULE_SRC
        hello = importlib.import_module("hello")
        self.assertIsNotNone(hello)
        self.assertTrue(hasattr(hello, 'greeting'))
        self.assertEqual(hello.greeting(), "Hellorld!")

class CodeLoadingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dbRootObj = tempfile.TemporaryDirectory()
        self.dbRoot = self.dbRootObj.name
        self.store = open_store(self.dbRoot)

        expr_text = "''.join(['hell', 'orld', '!!!!'])"
        self.expected = 'hellorld!!!!'
        self.expr_key = '/expr/hellorld'
        self.store[self.expr_key] = expr_text

    def tearDown(self) -> None:
        self.dbRootObj.cleanup()
    
    def test_eval_code_from_bailey(self):
        expr_text = self.store[self.expr_key]
        result = eval(expr_text)
        self.assertEqual(self.expected, result)


if __name__ == "__main__":
    unittest.main()