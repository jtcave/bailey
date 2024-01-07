import importlib.abc
from importlib.machinery import ModuleSpec
import importlib.util
from types import ModuleType
from typing import override
from .singleton import bailey
import os.path
import sys

def fullname_to_key(fullname: str):
    # TODO: permit configuration, multiple search paths, etc
    _SEARCH_KEY = '/py'
    subkey = fullname.replace('.', '/')
    key = os.path.join(_SEARCH_KEY, subkey)
    return key

class BaileyMetaPathFinder(importlib.abc.MetaPathFinder):
    _ORIGIN = "bailey"
    
    @classmethod
    def _search(cls, fullname):
        key = fullname_to_key(fullname)
        if key in bailey():
            return key
        else:
            return None

    @override
    @classmethod
    def find_spec(cls, fullname, path, target=None):
        # TODO: handle package `path`
        modulekey = cls._search(fullname)
        if modulekey is None: return None
        return importlib.util.spec_from_loader(fullname, BaileyLoader(), origin=modulekey)


class BaileyLoader(importlib.abc.Loader):
    @override
    def create_module(self, spec: ModuleSpec):
        # default implementation
        return None
    
    @override
    def exec_module(self, module: ModuleType):
        key = fullname_to_key(module.__name__)
        if key not in bailey():
            raise ImportError(f"bailey: can't find module {module.__name__} in bailey at {key}")
        try:
            source_text = bailey()[key]
        except Exception as exc:
            raise ImportError(f"bailey: could not load source for module {module.__name__} from {key}")
        mod_code = compile(source_text, filename=key, mode='exec')
        exec(mod_code, module.__dict__)

        

def install_loader():
    sys.meta_path.append(BaileyMetaPathFinder())