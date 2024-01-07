from .singleton import _bailey, bailey as bb, _BAILEY_URI
from .loader import install_loader

def bailey(uri=_BAILEY_URI):
    """Main entry point to bailey.
    Calling this returns a mapping you can use to """
    if not _bailey:
        install_loader()
    return bb(uri)