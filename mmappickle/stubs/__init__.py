__all__ = []

try:
    import numpy
    from .numpy import EmptyNDArray
    __all__.append('EmptyNDArray')
except ImportError:
    #No numpy, just ignore what would not be loadable
    pass
