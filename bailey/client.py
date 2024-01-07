import xmlrpc.client
from .backing.interface import PickleWrapper

class BaileyClient:
    def __init__(self, uri, *args, **kwds):
        self.proxy = xmlrpc.client.ServerProxy(uri, *args, allow_none=True, use_builtin_types=True, **kwds)

    def __getitem__(self, key):
        return self.proxy.get(key)
    
    def __setitem__(self, key, val):
        self.proxy.put(key, val)
    
    def __delitem__(self, key):
        self.proxy.delete(key)
    
    def __contains__(self, key):
        return self.proxy.present(key)
    
    def object_info(self, key: str):
        return self.proxy.info(key)

def connect(uri, *args, **kwds):
    client = BaileyClient(uri, *args, **kwds)
    store = PickleWrapper(client)
    return store
