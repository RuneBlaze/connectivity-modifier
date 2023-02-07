from functools import cached_property
import glob
from typing import Optional
from tomli import load
import os
import atexit
import shutil
import hashlib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Context:
    def __init__(self):
        self._working_dir = "hm01_working_dir"
        self.transient = False

    def with_working_dir(self, working_dir):
        self._working_dir = working_dir
        return self

    def as_transient(self):
        self.transient = True
        return self

    @property
    def ikc_path(self):
        return self.config["tools"]["ikc_path"].format(project_root=PROJECT_ROOT)

    @property
    def leiden_path(self):
        return self.config["tools"]["leiden_path"].format(project_root=PROJECT_ROOT)

    @property
    def viecut_path(self):
        return self.config["tools"]["viecut_path"].format(project_root=PROJECT_ROOT)

    @cached_property
    def config(self):
        lookup_paths = [
            "cm.toml",
            os.path.join(os.path.expanduser("~"), ".config", "cm", "config.toml"),
            os.path.join(os.path.dirname(__file__), "..", "default_config.toml"),
        ]
        for path in lookup_paths:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    return load(f)
        raise FileNotFoundError(
            "Config file not found in any of the following paths: "
            + ", ".join(lookup_paths)
        )

    @cached_property
    def working_dir(self):
        if not os.path.exists(self._working_dir):
            os.mkdir(self._working_dir)
        else:
            if self.transient:
                raise Exception("Working directory already exists under transient mode")
        if self.transient:
            atexit.register(lambda: shutil.rmtree(self._working_dir))
        return self._working_dir

    def request_graph_related_path(self, graph, suffix):
        return os.path.join(
            self.working_dir,
            hashlib.sha256(graph.index.encode("utf-8")).hexdigest()[:10] + "." + suffix,
        )

    def request_subpath(self, suffix) -> str:
        return os.path.join(self.working_dir, suffix)

    def find_latest_checkpoint(self) -> Optional[str]:
        checkpoints = glob.glob(os.path.join(self.working_dir, "*.pkl"))
        if not checkpoints:
            return None
        return max(checkpoints, key=os.path.getctime)


# we export the context as a singleton
context = Context()
