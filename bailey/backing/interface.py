from abc import abstractmethod, ABC
from typing import *
import pathlib
import pickle

# Win32 reserved characters <https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file>
# For cross-platform compatibility, keys may not use these characters.
INVALID_CHARS = "<>:\"/\\|?*" + ''.join(map(chr, range(32)))

# Win32 reserved device names. Keys may not use these names
INVALID_NAMES = ['CON', 'PRN', 'AUX', 'NUL', 'COM0', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'COM¹', 'COM²', 'COM³', 'LPT0', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9', 'LPT¹', 'LPT²', 'LPT³']

class InvalidKeyException(RuntimeError):
    pass

def test_key(keyPath: pathlib.PurePath):
    """Throws InvalidKeyException if the key is not acceptable"""
    if keyPath.name == "":
        # literally just /, or an empty path
        raise InvalidKeyException("key is empty")
    for part in keyPath.parts:
        if part != "/" and any(c in part for c in INVALID_CHARS):
            raise InvalidKeyException("key contains disallowed character")
        # TODO: reserved names with extensions (ex: CON.txt) are also proscribed
        if any(part == n for n in INVALID_NAMES):
            raise InvalidKeyException("key contains disallowed name")
        # no . or .. or ... (etc)
        if part.replace('.', '') == "":
            raise InvalidKeyException("key contains relative path specifier: " + part)

def produce_path(key: str) -> pathlib.PurePath:
    """Validates a key and emits a corresponding PurePath"""
    key_path = pathlib.PurePath(key)
    test_key(key_path)
    return key_path

class BaileyBacking(ABC):
    @abstractmethod
    def store(self, key: pathlib.PurePath, val: bytes):
        """Persists an object into the store. This replaces any existing object."""

    @abstractmethod
    def exists(self, key: pathlib.PurePath) -> bool:
        """Returns true if an object exists with the given key"""

    #@abstractmethod
    #def metadata(self, key: pathlib.PurePath) -> dict:
    #    """Returns metadata about the object"""
    #    # TODO: define a metadata type/schema

    @abstractmethod
    def fetch(self, key: pathlib.PurePath) -> bytes:
        """Retrieves an object from the store"""

    @abstractmethod
    def remove(self, key: pathlib.PurePath):
        """Erases object from the store"""
    
    @abstractmethod
    def __iter__(self) -> Iterator[str]:
        """Enumerates all keys in the store as strings"""
    
    # implement the Python collection interface as a mapping from str -> bytes
        
    def __getitem__(self, key: str) -> bytes:
        key_path = produce_path(key)
        return self.fetch(key_path)
    
    def __setitem__(self, key: str, val: bytes):
        key_path = produce_path(key)
        return self.store(key_path, val)
    
    def __delitem__(self, key: str):
        key_path = produce_path(key)
        return self.remove(key_path)
    
    def __contains__(self, key: str):
        key_path = produce_path(key)
        return self.exists(key_path)
    
    def object_info(self, key: str):
        key_path = produce_path(key)
        return self.metadata(key_path)

# shelve doesn't *exactly* do what we need, since it pickles the keys
class PickleWrapper:
    def __init__(self, backing):
        self.backing = backing

    def __getitem__(self, key: str) -> Any:
        pkl = self.backing[key]
        return pickle.loads(pkl)
    
    def __setitem__(self, key: str, val: Any):
        self.backing[key] = pickle.dumps(val)
    
    def __delitem__(self, key: str):
        del self.backing[key]
    
    def __contains__(self, key: str):
        return key in self.backing
    
    def __iter__(self):
        return iter(self.backing)
    
    def object_info(self, key: str):
        return self.backing.object_info(key)


def create_store(backing_class: Type, dbRoot: str):
    """Creates an instance of the backing_class, wraps it with PickleWrapper, and returns the wrapper"""
    return PickleWrapper(backing_class(dbRoot))