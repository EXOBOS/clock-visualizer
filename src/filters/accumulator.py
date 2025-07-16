"""
Copyright: 2025 Auxsys

A accumulator to combine multiple filters. Also responsible for handling
coloring, combinations, …
"""
from ..graphs import ClockType
from .abstractfilter import AbstractFilter, Property, State
from ..utils import Color

class FilterAccumulator:
    _color_dict = {
        State.HIDE: Color.from_hex("#0003"),
        State.SHOW: Color.from_hex("#a00"),
        State.UNKNOWN: Color.from_hex("#00F"),
        State.SPECIAL: Color.from_hex("#F00")
    }

    def __init__(self) -> None:
        self._filters: list[AbstractFilter] = []

    def add_filter(self, filter: AbstractFilter):
        self._filters.append(filter)

    def lookup_clock(self, clock: ClockType) -> Color | None:
        filter = self._filters[0]  # where are only using the first one for now

        return self._color_dict[filter.should_show_clock(clock)]

    def lookup_edge(self, n_from: ClockType, n_to: ClockType) -> Color | None:
        filter = self._filters[0]  # where are only using the first one for now

        return self._color_dict[filter.should_show_edge(n_from, n_to)]

    def lookup_clock_properties(self, clock: ClockType) -> list[Property]:
        return [
            prop for filter in self._filters
            if (prop := filter.get_clock_property(clock)) is not None
        ]
