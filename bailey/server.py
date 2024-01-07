import xmlrpc.server
from .backing.interface import BaileyBacking
from .backing.fspickle import BaileyBackingFsPickle

class BaileyService:
    """shim class to expose a store"""
    def __init__(self, backing: BaileyBacking):
        self._backing = backing
    
    def get(self, key: str):
        return self._backing[key]
    
    def put(self, key: str, val: bytes):
        self._backing[key] = val
        return key
    
    def delete(self, key: str):
        del self._backing[key]
        return key
    
    def present(self, key: str):
        return key in self._backing
    
    def info(self, key: str):
        return self._backing.object_info(key)

def start_server(dbRoot, addr=('localhost', 8080), *args, **kwds):
    """Starts the Bailey server. This will block."""
    with xmlrpc.server.SimpleXMLRPCServer(addr, *args, allow_none=True, use_builtin_types=True, **kwds) as server:
        store = BaileyBackingFsPickle(dbRoot)
        service = BaileyService(store)
        server.register_introspection_functions()
        server.register_instance(service)
        server.serve_forever()

if __name__ == "__main__":
    # TODO: allow user configuration
    dbRoot = "/tmp/bailey"
    addr = ('localhost', 8080)
    print(f"serving objects from {dbRoot} at {addr[0]}:{addr[1]}")
    try:
        start_server('/tmp/bailey')
    except KeyboardInterrupt:
        pass