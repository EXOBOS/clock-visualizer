"""
Copyright: 2025 Auxsys

Custom yaml object extensions. These are mostly for the tags
"""
import yaml
# we don't need the speed from the c parser
from yaml import Loader, Dumper

from enum import Enum

class AddrObject(yaml.YAMLObject):
    class Endianess(Enum):
        UNKNOWN = None
        LE = "little"
        BE = "big"

    yaml_loader = Loader
    yaml_dumper = Dumper

    width = 0
    endianess = Endianess.UNKNOWN

    def __init__(self, addr, bit) -> None:
        self.addr: int = addr
        self.bit: tuple[int] | tuple[int, int] = bit

        if len(self.bit) not in [1, 2]:
            raise ValueError(f"bit must be a tuple of one or two elements ({self})")
        if len(self.bit) == 2 and self.bit[0] <= self.bit[1]:
            raise ValueError(f"bit ({self.bit}) is not strictly monotonly decreasing")
        if self.endianess == AddrObject.Endianess.UNKNOWN:
            raise NotImplementedError("This class should not be initialized directly")

    def __str__(self) -> str:
        return f"AddrObject{self.width}(0x{self.addr:X}, {self.bit}, {self.endianess})"

    @classmethod
    def from_yaml(cls, loader, node):
        addr, bit = loader.construct_sequence(node, deep=True)
        return cls(addr, bit)

    def to_json(self):
        return [self.addr, self.bit]

class AddrObject32LE(AddrObject):
    width = 32
    endianess = AddrObject.Endianess.LE
    yaml_tag = "!addr32le"

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


