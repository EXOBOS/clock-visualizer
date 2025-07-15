"""
Copyright: 2025 Auxsys

abstract class to define interface of filter
"""
from abc import ABC, abstractmethod
from ..clkdesc import ClockType
from enum import Enum, auto

class State(Enum):
    UNKNOWN = None
    HIDE = 0
    SHOW = 1
    SPECIAL = 2

class Property:
    ...

class AbstractFilter(ABC):
    """
    Abstract filter class that defines the interface

    The nodes and edges of the clock graph can be looked up in this class
    returning a boolean value depending on whether to hide, show, … the
    node/edge. Other interpretations like coloring and such are
    responsibilities for others e.g. accumulator.
    """

    @abstractmethod
    def should_show_clock(self, clk: ClockType) -> State:
        ...

    @abstractmethod
    def should_show_edge(self, n_from: ClockType, n_to: ClockType) -> State:
        ...

    @abstractmethod
    def get_clock_property(self, clk: ClockType) -> Property | None:
        ...
