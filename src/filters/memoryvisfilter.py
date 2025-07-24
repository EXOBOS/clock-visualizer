"""
Copyright: 2025 Auxsys

Clock "filter" that is mainly used to inject properties into the accumulation
filter from the memory graph. It does not manipulate the graph.
"""

from ..graphs import MemoryClockGraph, ClockType
from ..graphs.memoryclockgraph import ParsedMux, ParsedClock
from .abstractfilter import AbstractFilter, Property, State
from dataclasses import dataclass

@dataclass(frozen=True)
class MemPropertyMux(Property):
    selected: int

@dataclass(frozen=True)
class MemPropertyIsEnabled(Property):
    is_enabled: bool

@dataclass(frozen=True)
class MemPropertyRegisters(Property):
    registers: dict[int, tuple[int, int]]


class MemoryVisFilter(AbstractFilter):
    def __init__(self, graph: MemoryClockGraph):
        self._graph = graph

    def should_show_clock(self, clk: ClockType) -> State:
        return State.SHOW

    def should_show_edge(self, n_from: ClockType, n_to: ClockType) -> State:
        return State.SHOW

    def get_clock_properties(self, clk: ClockType) -> list[Property] | None:
        props = []
        parsed_node = self._graph.get_parsed_for_clk(clk)

        match parsed_node:
            case ParsedMux():
                props.append(MemPropertyMux(parsed_node.choosen))
            case ParsedClock():
                props.append(MemPropertyIsEnabled(parsed_node.is_enabled))
            case _:
                ...

        props.append(MemPropertyRegisters(self._graph.get_registers(clk)))

        return props

