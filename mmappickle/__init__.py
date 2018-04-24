from .dict import mmapdict
__all__ = ['mmapdict']

try:
    from .http import httpdict
    __all__.append('httpdict')
except ImportError:
    #Ignore missing dependencies, like requests
    pass


