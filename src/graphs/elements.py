"""
Copyright: 2025 Auxsys

Elements of the clock graph
"""
from dataclasses import dataclass

from .yamlobjects import AddrObject

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
    is_enabled: None | tuple[dict[int, bool], AddrObject]
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


