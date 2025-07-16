"""
Copyright: 2025 Auxsys

Abstract class representing a graph
"""
from abc import ABC, abstractmethod
from typing import Iterator

from .elements import ClockType

class AbstractGraph(ABC):

    @abstractmethod
    def get_clk(self, name: str) -> ClockType | None:
        ...

    @abstractmethod
    def get_clks(self) -> Iterator[ClockType]:
        ...

    @abstractmethod
    def get_input_clks(self) -> set[ClockType]:
        """These are clocks that don't have an input themselves"""
        ...

    @abstractmethod
    def get_output_clks(self) -> set[ClockType]:
        """These are clocks that are not connected anywhere else"""
        ...

    @abstractmethod
    def list_outputs_for_clk(self, clk: ClockType) -> set[ClockType]:
        ...

    @abstractmethod
    def list_inputs_for_clk(self, clk: ClockType) -> list[ClockType]:
        ...
