from .client import connect

# bailey singleton
# TODO: proper configuration
_bailey = None
_BAILEY_URI = "http://localhost:8080"
def bailey(uri=_BAILEY_URI):
    global _bailey
    if _bailey is None:
        _bailey = connect(uri)
    return _bailey