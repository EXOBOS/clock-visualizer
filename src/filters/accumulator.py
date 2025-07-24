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
        opinions = [filter.should_show_clock(clock) for filter in self._filters]

        if State.SPECIAL in opinions:
            return self._color_dict[State.SPECIAL]
        if State.HIDE in opinions:
            return self._color_dict[State.HIDE]
        return self._color_dict[State.SHOW]

    def lookup_edge(self, n_from: ClockType, n_to: ClockType) -> Color | None:
        opinions = [filter.should_show_edge(n_from, n_to) for filter in self._filters]

        if State.SPECIAL in opinions:
            return self._color_dict[State.SPECIAL]
        if State.HIDE in opinions:
            return self._color_dict[State.HIDE]
        return self._color_dict[State.SHOW]

    def lookup_clock_properties(self, clock: ClockType) -> dict[type[Property], Property]:
        prop_dict = {}

        for filter in self._filters:
            if (props := filter.get_clock_properties(clock)) is not None:
                for prop in props:
                    assert prop.__class__ not in prop_dict

                    prop_dict[prop.__class__] = prop
        return prop_dict
