"""
Copyright: 2025 Auxsys

Child of clock graph, that changes the graph according to the clock
configuration represented by a memory dump. Significant alterations to the
graph are due to the way muxes are configured or whether clocks are enabled or
not.
"""
from ..utils import SparseMemory
from .elements import ClockType, Clock, Mux, Div
from .clockgraph import ClockGraph
from .abstractgraph import AbstractGraph
from dataclasses import dataclass
from typing import Iterator

@dataclass
class ParsedClockType:
    ...

@dataclass
class ParsedClock(ParsedClockType):
    is_enabled: bool

@dataclass
class ParsedPll(ParsedClock):
    ...

@dataclass
class ParsedMux(ParsedClockType):
    choosen: int

@dataclass
class ParsedDiv(ParsedClockType):
    value: float

class MemoryClockGraph(AbstractGraph):
    def __init__(self, graph: ClockGraph, memory: SparseMemory) -> None:
        self._graph = graph
        self._memory = memory
        self._parsednodes: dict[ClockType, ParsedClockType] = self._preprocess()

    def _preprocess(self) -> dict[ClockType, ParsedClockType]:
        parsednodes = {}
        for node in self._graph.get_clks():
            match node:
                case Clock():
                    parsed = ParsedClock(node.parse(self._memory))
                case Mux():
                    parsed = ParsedMux(node.parse(self._memory))
                case Div():
                    parsed = ParsedDiv(-1)
                case _:
                    raise NotImplementedError(f"Node type not yet implemented ({node})")

            parsednodes[node] = parsed
        return parsednodes

    def get_clk(self, name: str) -> ClockType | None:
        ...

    def get_clks(self) -> Iterator[ClockType]:
        ...

    def get_input_clks(self) -> set[ClockType]:
        """These are clocks that don't have an input themselves"""
        ...

    def get_output_clks(self) -> set[ClockType]:
        """These are clocks that are not connected anywhere else"""
        ...

    def list_outputs_for_clk(self, clk: ClockType) -> set[ClockType]:
        ...

    def list_inputs_for_clk(self, clk: ClockType) -> list[ClockType]:
        ...
