"""
Copyright: 2025 Auxsys

Clock graph description structure and respective parser
"""
from typing import TextIO, Callable, Iterator
from pathlib import Path
from dataclasses import dataclass
import json
import jsonschema

import yaml
from yaml import Loader, Dumper  # we don't need the speed from the c parser

class AddrObject(yaml.YAMLObject):
    yaml_loader = Loader
    yaml_dumper = Dumper

    yaml_tag = "!addr"

    def __init__(self, addr, bit) -> None:
        self.addr = addr
        self.bit = bit

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

@dataclass()
class ClockType():
    name: str
    description: str

    def list_inputs(self) -> None | list["ClockType"]:
        raise NotImplementedError()

    def __hash__(self) -> int:
        return self.name.__hash__()

@dataclass()
class Clock(ClockType):
    is_enabled: None | tuple[dict, AddrObject]
    input: None | ClockType

    def list_inputs(self) -> None | list[ClockType]:
        return [self.input] if self.input else None

    def __hash__(self) -> int:
        return self.name.__hash__()

@dataclass()
class Pll(Clock):
    ...

    def __hash__(self) -> int:
        return self.name.__hash__()

@dataclass()
class Mux(ClockType):
    register: AddrObject
    inputs: dict[int, None | ClockType]

    def list_inputs(self) -> None | list[ClockType]:
        return [ ins for ins in self.inputs.values() if ins is not None ]

    def __hash__(self) -> int:
        return self.name.__hash__()

@dataclass()
class Div(ClockType):
    input: ClockType
    value: Callable[[list[int]], float]
    registers: dict[str, AddrObject]

    def list_inputs(self) -> None | list[ClockType]:
        return [self.input]

    def __hash__(self) -> int:
        return self.name.__hash__()

class ClockGraph:
    def __init__(self, name, vendor, clocks) -> None:
        self.name = name
        self.vendor = vendor
        self.clocks = clocks

    def get_clk(self, name: str) -> ClockType | None:
        return self.clocks.get(name)

    def get_clks(self) -> Iterator[ClockType]:
        return self.clocks.values()

    def get_input_clks(self) -> set[ClockType]:
        """These are clocks that don't have an input themselves"""
        return { clk for clk in self.get_clks() if isinstance(clk, Clock) and clk.input is None }

    def get_output_clks(self) -> set[ClockType]:
        """These are clocks that are not connected anywhere else"""
        clocks: set[ClockType] = { clk for clk in self.get_clks() if isinstance(clk, Clock) }
        is_used: set[ClockType] = set()
        for clk in self.clocks.values():
            if clk.list_inputs() is not None:
                is_used.update(clk.list_inputs())

        return clocks - is_used

    def list_outputs_for_clk(self, clk: ClockType) -> set[ClockType]:
        outputs: set[ClockType] = set()

        for oclk in self.clocks.values():
            if (l := oclk.list_inputs()) is not None and clk in l:
                outputs.add(oclk)

        return outputs

    ################
    # Data Parsing #
    ################

    @staticmethod
    def validate_data(schema: dict, data: dict):
        def sanitize_data(obj: object):
            if isinstance(obj, dict):
                return {str(k): sanitize_data(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_data(v) for v in obj]
            elif isinstance(obj, AddrObject):
                return obj.to_json()
            elif isinstance(obj, LambdaObject):
                return obj.original
            else:
                return obj

        json_valid_data = sanitize_data(data)
        jsonschema.validate(instance=json_valid_data, schema=schema)


    @classmethod
    def from_yaml(cls, soc_file: TextIO, schema_file: str | Path | None = Path(__file__).parent / "../../socs/soc.schema.json"):
        soc_data = soc_file.read()

        def tag_add_constructor(loader: Loader, node):
            value: list[int] = loader.construct_sequence(node)
            return sum(value)

        yaml.add_constructor("!add", tag_add_constructor, Loader=Loader)
        soc_data = yaml.load(soc_data, Loader=Loader)

        # validate the data (if schema is available)
        if schema_file is not None:
            schema_file = Path(schema_file)
            with schema_file.open("r") as fp:
                try:
                    cls.validate_data(json.load(fp), soc_data)
                except jsonschema.ValidationError as e:
                    raise Exception(f"Yaml failed validation using schema `{schema_file}`", e)

        # transform data into our format
        clocks = dict()
        for element in soc_data["clocks"]:
            name = next(iter(element))
            data = element[name]

            item = None
            if data["type"] == "clk" or data["type"] == "pll":
                is_enabled = tuple(data["is_enabled"]) if "is_enabled" in data else None

                mcls = Clock if data["type"] == "clk" else Pll

                item = mcls(
                    name=name, description=data["desc"],
                    is_enabled=is_enabled,
                    input=data.get("input", None)
                )
            elif data["type"] == "mux":
                item = Mux(
                    name=name, description=data["desc"],
                    register=data["reg"],
                    inputs={ k: None if v == "RESERVED" else v for k,v in data["input"].items() }
                )
            elif data["type"] == "div":
                registers = {
                     key.lstrip("r_"):value for key, value in data.items()
                     if isinstance(key, str) and key.startswith("r_")
                }

                item = Div(
                    name=name, description=data["desc"],
                    input=data["input"],
                    value=data["value"],
                    registers=registers
                )

            clocks[name] = item

        # reiterate over the list to apply crossreferences
        for clock in clocks.values():
            if isinstance(clock, Clock):
                clock.input = clocks.get(clock.input, None)
            elif isinstance(clock, Mux):
                clock.inputs = { k: clocks[name] if name else None  for k, name in clock.inputs.items() }
            elif isinstance(clock, Div):
                clock.input = clocks[clock.input]
            else:
                raise NotImplementedError(f"Missing type {clock.__class__}")

        return cls(soc_data["name"], soc_data["vendor"], clocks)
