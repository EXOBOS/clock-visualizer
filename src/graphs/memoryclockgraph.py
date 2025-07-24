"""
Copyright: 2025 Auxsys

Child of clock graph, that changes the graph according to the clock
configuration represented by a memory dump. Significant alterations to the
graph are due to the way muxes are configured or whether clocks are enabled or
not.
"""
from ..utils import SparseMemory
from .elements import ClockType, Clock, Mux, Div, Pll
from .clockgraph import ClockGraph
from .abstractgraph import AbstractGraph
from dataclasses import dataclass
from typing import Iterator

@dataclass(frozen=True)
class ParsedClockType:
    origin: ClockType

@dataclass(frozen=True)
class ParsedClock(ParsedClockType):
    origin: Clock
    is_enabled: bool

@dataclass(frozen=True)
class ParsedPll(ParsedClock):
    origin: Pll

@dataclass(frozen=True)
class ParsedMux(ParsedClockType):
    origin: Mux
    choosen: int

@dataclass(frozen=True)
class ParsedDiv(ParsedClockType):
    origin: Div
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
                    parsed = ParsedClock(node, node.parse(self._memory))
                case Mux():
                    parsed = ParsedMux(node, node.parse(self._memory))
                case Div():
                    parsed = ParsedDiv(node, -1)
                case _:
                    raise NotImplementedError(f"Node type not yet implemented ({node})")

            parsednodes[node] = parsed
        return parsednodes

    def get_clk(self, name: str) -> ClockType | None:
        return self._graph.get_clk(name)

    def get_clks(self) -> Iterator[ClockType]:
        return self._graph.get_clks()

    def get_input_clks(self) -> set[ClockType]:
        """These are clocks that don't have an input themselves"""
        return self._graph.get_input_clks()

    def get_output_clks(self) -> set[ClockType]:
        """These are clocks that are not connected anywhere else"""
        return self._graph.get_output_clks()

    def list_outputs_for_clk(self, clk: ClockType) -> set[ClockType]:
        unfiltered_outs = self._graph.list_outputs_for_clk(clk)

        if isinstance(mclk := self._parsednodes[clk], ParsedClock) \
                and not mclk.is_enabled:
            return set()

        def is_connected(nclk: ClockType) -> bool:
            pclk: ParsedClockType = self._parsednodes[nclk]

            match pclk:
                case ParsedMux():
                    return clk == pclk.origin.inputs.get(pclk.choosen, None)
                case _:
                    return True

        return set(filter(is_connected, unfiltered_outs))

    def list_inputs_for_clk(self, clk: ClockType) -> list[ClockType]:
        parsed = self._parsednodes[clk]
        match parsed:
            case ParsedMux():
                v = parsed.origin.inputs.get(parsed.choosen, None)
                return [] if v is None else [v]
            case _:
                ins = self._graph.list_inputs_for_clk(clk)
                assert len(ins) <= 1, f"There should be only one input for clk {parsed}. Got {ins}"
                return ins

    def get_parsed_for_clk(self, clk: ClockType) -> ParsedClockType:
        return self._parsednodes[clk]

    def get_registers(self, clk: ClockType) -> dict[int, tuple[int, int]]:
        regs = dict()

        for reg in clk.used_registers:
            reg.bit = (reg.width, 0)
            regs[reg.addr] = (self._memory.get_register(reg), reg.width)

        return regs

