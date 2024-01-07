from .fspickle import BaileyBackingFsPickle
from .interface import create_store

def open_store(dbRoot: str):
    return create_store(BaileyBackingFsPickle, dbRoot)

__all__ = ['open_store']