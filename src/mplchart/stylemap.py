"""mplchart stylemap (experimental)"""

from collections import Counter, ChainMap
from typing import Union


class StyleMap:
    def __init__(self, mapping, counter: Counter = None):
        if not isinstance(mapping, ChainMap):
            mapping = ChainMap(mapping)
        if counter is None:
            counter = Counter()

        self.mapping = mapping
        self.counter = counter

    def merge(self, mapping, *, reset: bool = False):
        mapping = self.mapping.new_child(mapping)
        counter = Counter() if reset else self.counter
        return self.__class__(mapping, counter)

    def copy(self, *, reset: bool = True):
        mapping = self.mapping
        counter = Counter() if reset else self.counter
        return self.__class__(mapping, counter)

    def __repr__(self):
        cname = self.__class__.__name__
        return f"{cname}({self.mapping!r}, {self.counter!r})"

    @staticmethod
    def check_prefix(prefix) -> list:
        if isinstance(prefix, list):
            return prefix
        if isinstance(prefix, str):
            return prefix.split(":")
        raise TypeError(f"Invalid prefix {prefix!r}")

    def get_setting(self, prefix: Union[str, list], name: str, default=None):
        prefix = self.check_prefix(prefix)

        for p in prefix:
            key = p + ":" + name
            value = self.mapping.get(key)
            if isinstance(value, list) and len(value):
                count = self.counter[key]
                value = value[count % len(value)]
                self.counter[key] += 1
            if value is not None:
                return value

        return default

    def get_settings(self, prefix: Union[str, list], **kwds):
        prefix = self.check_prefix(prefix)

        for name, value in kwds.items():
            value = self.get_setting(prefix, name, value)
            kwds[value] = value
