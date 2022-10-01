from functools import cached_property
from tomli import load
import os
class Context:
    def __init__(self):
        self._working_dir = "hm01_working_dir"
    
    def with_working_dir(self, working_dir):
        self._working_dir = working_dir
        return self

    @property
    def ikc_path(self):
        return self.config["tools"]["ikc_path"]

    @property
    def leiden_path(self):
        return self.config["tools"]["leiden_path"]
    
    @cached_property
    def config(self):
        lookup_paths = [
            "hm01.toml",
            os.path.join(os.path.expanduser("~"), ".config", "hm01", "config.toml"),
            os.path.join(os.path.dirname(__file__), "..", "default_config.toml"),
        ]
        for path in lookup_paths:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    return load(f)
        raise FileNotFoundError("Config file not found in any of the following paths: " + ", ".join(lookup_paths))
    
    @cached_property
    def working_dir(self):
        if not os.path.exists(self._working_dir):
            os.mkdir(self._working_dir)
        return self._working_dir

# we export the context as a singleton
context = Context()