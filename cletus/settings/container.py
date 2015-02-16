"""
Cletus settings container
"""
from types import ModuleType

MODULE_PREFIX = 'module:'


class Settings(object):
    """
    Settings container
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise settings
        
        Arguments:
            *args       Settings sources
            **kwargs    Settings values
        """
        self.__dict__['_settings'] = {}
        self.load(*args)
        self.__dict__['_settings'] = kwargs
    
    def __getattr__(self, name):
        if name in self._settings:
            return self._settings[name]
        raise AttributeError(name)
    
    def __setattr__(self, name, val):
        if name.startswith('_'):
            raise AttributeError(name)
        self._settings[name] = val
    
    def __add__(self, settings):
        """
        Return a new Settings object with the settings from this, overridden
        by the settings on the second specified Settings object
        """
        if not isinstance(settings, Settings):
            raise ValueError('Can only add Settings objects to each other')
        dct = {}
        dct.update(self._settings)
        dct.update(settings._settings)
        return Settings(**dct)
    
    def update(self, dct):
        if isinstance(dct, Settings):
            dct = dct._settings
        self._settings.update(dct)
        
    def load(self, *sources):
        """
        Load settings from the specified sources to override these settings
        
        Accepted sources:
            module                  Reference to imported module
            "module:python.module"  Name of python module to import
            "/path/to/conf.json"    Path to JSON file
        """
        for source in sources:
            if isinstance(source, ModuleType):
                self.load_module(source)
            elif source.startswith(MODULE_PREFIX):
                module = __import__(source[len(MODULE_PREFIX):])
                self._load_module(module)
            elif source.endswith('.json'):
                self._load_json(source)
            else:
                raise ValueError('Unknown settings source: %s' % source)
    
    def load_module(self, module):
        """
        Load settings from imported python module to override these settings
        """
        dct = {
            key: getattr(module, key)
            for key
            in (module.__all__ if hasattr(module, '__all__') else dir(module))
            if not key.startswith('_')
        }
        self.update(dct)
    
    def load_json(cls, path):
        """
        Load settings from specified JSON file to override these settings
        """
        import json
        with open(path, 'r') as f:
            raw = f.read()
        dct = json.loads(raw)
        self.update(dct)