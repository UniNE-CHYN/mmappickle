from .base import GenericPickler

__all__ = ['GenericPickler']

try:
    import numpy
    from .numpy import MaskedArrayPickler, ArrayPickler
    __all__.append('ArrayPickler')
    __all__.append('MaskedArrayPickler')
except ImportError:
    #No numpy, just ignore what would not be loadable
    pass
