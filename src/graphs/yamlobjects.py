"""
Copyright: 2025 Auxsys

Custom yaml object extensions. These are mostly for the tags
"""
import yaml
# we don't need the speed from the c parser
from yaml import Loader, Dumper

from enum import Enum

class AddrObject(yaml.YAMLObject):
    yaml_loader = Loader
    yaml_dumper = Dumper

    yaml_tag = "!addr"

    def __init__(self, addr, bit) -> None:
        self.addr: int = addr
        self.bit: tuple[int] | tuple[int, int] = bit

    @classmethod
    def from_yaml(cls, loader, node):
        addr, bit = loader.construct_sequence(node)
        return cls(addr, bit)

    def to_json(self):
        return [self.addr, self.bit]

class LambdaObject(yaml.YAMLObject):
    yaml_loader = Loader
    yaml_dumper = Dumper

    yaml_tag = "tag:yaml.org,2002:lambda"

    def __init__(self, original: str) -> None:
        self.original = original

    def __call__(self, ins: list[int]) -> int:
        raise NotImplementedError("Not yet implemented")

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(loader.construct_yaml_str(node))


