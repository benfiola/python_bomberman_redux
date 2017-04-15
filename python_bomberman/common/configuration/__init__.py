import json


class Configuration(object):
    def __init__(self, defaults, config_file, root=None):
        self.root = root
        self.defaults = defaults
        self.current = None
        self.config_file = config_file

        # Will load, then immediately save.  This way it will immediately persist any correction _load performed.
        self._load()
        self.save()

    def get(self, key):
        if key not in self.current:
            raise ConfigurationException.key_not_found(key)
        return self.current[key]

    def set(self, key, value):
        if key not in self.current:
            raise ConfigurationException.key_not_found(key)
        self.current[key] = value

    def save(self):
        """
        Save will save the current configuration to a file.  
        
        First, it reads from the file so that it only writes the subdict relevant to this particular configuration.
        """
        config_dict = self._read_from_file()

        if self.root:
            config_dict[self.root] = self.current
        else:
            config_dict = self.current

        with open(self.config_file, 'w') as f:
            f.write(json.dumps(
                config_dict,
                sort_keys=True,
                indent=4,
                separators=(',', ': ')
            ))

    def _load(self):
        """
        Load will load a configuration from a file and set self.current to a dictionary representing the loaded data.
        
        It will also prune keys that aren't present in the default values, and add default values that don't exist in
        the loaded data prior to setting self.current
        """
        config_dict = self._read_from_file()

        if self.root and self.root not in config_dict:
            self.current = self.defaults
            return

        if self.root is not None:
            config_dict = config_dict[self.root]

        # keys to remove
        for key in list(filter(lambda k: k not in self.defaults, config_dict.keys())):
            config_dict.pop(key)

        # keys to add
        for key in list(filter(lambda k: k not in config_dict, self.defaults)):
            config_dict[key] = self.defaults[key]

        self.current = config_dict

    def _read_from_file(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.loads(f.read())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}


class ConfigurationException(Exception):
    def __init__(self, *args):
        super().__init__(*args)

    @classmethod
    def key_not_found(cls, k):
        return cls("Key {} not found in configuration".format(k))
