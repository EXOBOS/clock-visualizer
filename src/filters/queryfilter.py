"""
Copyright: 2025 Auxsys

Clock filter using a clock name
"""
from ..graphs import AbstractGraph, ClockType
from .abstractfilter import AbstractFilter, Property, State

class QueryFilter(AbstractFilter):
    def __init__(self, graph: AbstractGraph, query: ClockType,
                 show_inputs: bool = True, show_outputs: bool = True) -> None:
        # it is okay here to pass the graph as the 'lifetime' of it is longer than this class
        self._graph = graph
        self._query = query

        # build filtered node set
        self._filtered_graph: set[ClockType] = set()

        ## find all predecessors / inputs
        def find_predecessors(path: list[ClockType]) -> set[ClockType]:
            """I am aware that this is not efficient, but our graphs are small"""
            all_inputs = {path[-1]}
            if (inputs := graph.list_inputs_for_clk(path[-1])) is not None:
                for inp in inputs:
                    if inp in path:
                        raise Exception(f"Loop found in clk graph. See node `{inp}`")

                    all_inputs.update(find_predecessors([*path, inp]))

            return all_inputs

        if show_inputs:
            self._filtered_graph.update(find_predecessors([self._query]))

        ## find all successors / outputs
        def find_successors(graph: AbstractGraph, path: list[ClockType]) -> set[ClockType]:
            """I am aware that this is not efficient, but our graphs are small"""
            all_outputs = {path[-1]}

            for out in graph.list_outputs_for_clk(path[-1]):
                if out in path:
                    raise Exception(f"Loop found in clk graph. See node `{out}`")
                all_outputs.update(find_successors(graph, [*path, out]))

            return all_outputs

        if show_outputs:
            self._filtered_graph.update(find_successors(self._graph, [self._query]))

    def should_show_clock(self, clk: ClockType) -> State:
        if clk == self._query:
            return State.SPECIAL

        if clk in self._filtered_graph:
            return State.SHOW
        else:
            return State.HIDE

    def should_show_edge(self, n_from: ClockType, n_to: ClockType) -> State:
        if n_from in self._filtered_graph and n_to in self._filtered_graph:
            if n_from in self._graph.list_inputs_for_clk(n_to):
                return State.SHOW
        return State.HIDE

    def get_clock_properties(self, clk: ClockType) -> list[Property] | None:
        return None
