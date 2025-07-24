"""
Copyright: 2025 Auxsys

Elements of the clock graph
"""
from __future__ import annotations
from typing import Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from ..utils import SparseMemory

from dataclasses import dataclass
from copy import deepcopy

from .yamlobjects import AddrObject

@dataclass()
class ClockType():
    name: str
    description: str

    @property
    def used_registers(self) -> set[AddrObject]:
        return set()

    def list_inputs(self) -> None | list["ClockType"]:
        raise NotImplementedError()

    def __hash__(self) -> int:
        return self.name.__hash__()

@dataclass()
class Clock(ClockType):
    is_enabled: None | tuple[dict[int, bool], AddrObject]
    input: None | ClockType

    @property
    def used_registers(self) -> set[AddrObject]:
        regs = super().used_registers
        if self.is_enabled is not None:
            regs.add(self.is_enabled[1])
        return deepcopy(regs)

    def list_inputs(self) -> None | list[ClockType]:
        return [self.input] if self.input else None

    def parse(self, memory: SparseMemory) -> bool:
        if self.is_enabled is None:
            return True
        value, addr = self.is_enabled
        if len(addr.bit) != 1:
            raise ValueError(f"Invalid bits ({addr.bit}) for this operation [required len=1]")
        return value[memory.get_register(addr)]

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

    @property
    def used_registers(self) -> set[AddrObject]:
        regs = super().used_registers
        regs.add(self.register)
        return deepcopy(regs)

    def list_inputs(self) -> None | list[ClockType]:
        return [ ins for ins in self.inputs.values() if ins is not None ]

    def parse(self, memory: SparseMemory) -> int:
        return memory.get_register(self.register)

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

    @property
    def used_registers(self) -> set[AddrObject]:
        regs = super().used_registers
        regs.update(reg for reg in self.registers.values())
        return deepcopy(regs)


