import pickle
import pickle
import pathlib

from .interface import *

def graft_key_to_db_root(dbRoot: pathlib.Path, keyPath: pathlib.PurePath) -> pathlib.Path:
    """Produces an absolute path to the object that the keyPath would refer to.
    It is assumed that keyPath is valid"""
    if keyPath.is_absolute():
        keySubpath = keyPath.parts[1:]
    else:
        keySubpath = keyPath.parts
    return dbRoot.joinpath(*keySubpath)
 
def path_for_key(dbRoot: pathlib.Path, key: str) -> pathlib.Path:
    key_path = pathlib.PurePath(key)
    test_key(key_path)
    return graft_key_to_db_root(dbRoot, key_path)

class BaileyBackingFsPickle(BaileyBacking):
    def __init__(self, dbRoot: str):
        self.dbRoot = pathlib.Path(dbRoot)
        if not self.dbRoot.exists():
            raise FileNotFoundError("db root not found", str(self.dbRoot))
        if not self.dbRoot.is_dir():
            raise NotADirectoryError("db root is not a directory", str(self.dbRoot))
    
    @override
    def store(self, key: pathlib.PurePath, val: bytes):
        """Persists an object into the store. This replaces any existing object."""
        fs_path = path_for_key(self.dbRoot, key)
        try:
            fs_path.write_bytes(val)
        except FileNotFoundError:
            # automatically create superkey(s) of the specified key
            superkey = key.parent
            superkey_path = path_for_key(self.dbRoot, superkey)
            superkey_path.mkdir(parents=True)
            fs_path.write_bytes(val)

    @override
    def exists(self, key: pathlib.PurePath) -> bool:
        """Returns true if an object exists with the given key"""
        fs_path = path_for_key(self.dbRoot, key)
        return fs_path.exists()

    #@override
    #def metadata(self, key: pathlib.PurePath) -> dict:
    #    """Returns metadata about the object"""
    #    # TODO: define a metadata type/schema

    @override
    def fetch(self, key: pathlib.PurePath) -> bytes:
        """Retrieves an object from the store"""
        fs_path = path_for_key(self.dbRoot, key)
        try:
            return fs_path.read_bytes()
        except IsADirectoryError:
            # just enumerate the subkeys and pickle the list
            matches = fs_path.iterdir()
            subkeys = [str(match.name) for match in matches]
            return pickle.dumps(subkeys)
            
            

    @override
    def remove(self, key: pathlib.PurePath):
        """Erases object from the store"""
        fs_path = path_for_key(self.dbRoot, key)
        fs_path.unlink()
    
    @override
    def __iter__(self):
        # TODO: maybe use the Path.walk method?
        for match in self.dbRoot.rglob("*"):
            key_path = match.relative_to(self.dbRoot)
            key = str(key_path)
            yield key