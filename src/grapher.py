"""
Copyright: 2025 Auxsys

Using the tree and a respective highlighting node, this will
graph the tree using graphviz.
"""
import graphviz

from .filters import FilterAccumulator
from .graphs import ClockGraph, Clock, ClockType, Div, Mux

class Grapher():
    def __init__(self, clocks: ClockGraph, filters: FilterAccumulator) -> None:
        self.clocks = clocks
        self.filters = filters

        self.build_raw_graph()
        print(self.graph.source)

    def add_edge(self, graph: graphviz.Digraph, clk_from: ClockType, clk_to: ClockType):
        if self.filters.lookup_edge(clk_from, clk_to) is None:
            return

        from_s = clk_from.name
        if isinstance(clk_from, Mux):
            from_s += ":out"

        to_s = clk_to.name
        if isinstance(clk_to, Mux):
            to_s += f":{clk_from.name}"

        graph.edge(from_s + ":e", to_s + ":w", color=str(self.filters.lookup_edge(clk_from, clk_to)))

    def build_raw_graph(self):
        graph = graphviz.Digraph(
            node_attr={"shape": "record"},
            graph_attr={"splines": "polyline", "ranksep":"3", "rankdir": "LR", "newrank": "true"}
        )

        # add nodes
        for clk in self.clocks.get_clks():
            if self.filters.lookup_clock(clk) is None:
                continue

            if isinstance(clk, Mux):
                with graph.subgraph(name=f"cluster_{clk.name}", graph_attr={"labelloc": "b", "color": "none", "label": clk.name}) as g:
                    _inputs = []
                    _defaults = []
                    for k, sclk in clk.inputs.items():
                        if not sclk:
                            continue
                        if k != "default":
                            _inputs.append(f"<{sclk.name}> {k:b}")
                        else:
                            _defaults.append(sclk)


                    if len(_defaults) > 0:
                        _inputs.append(
                            ("".join(f"<{c.name}>" for c in _defaults))
                            + "default"
                        )

                    struct_desc = f"{{{{{ '|'.join(_inputs) }}}|<out> out}}"
                    g.node(clk.name, struct_desc, color=str(self.filters.lookup_clock(clk)))
            elif isinstance(clk, Clock) or isinstance(clk, Div):
                graph.node(clk.name, clk.name, color=str(self.filters.lookup_clock(clk)))
            else:
                raise NotImplementedError(f"Missing type {clk.__class__}")

        # add edges
        for clk in self.clocks.get_clks():
            if isinstance(clk, Mux):
                for inp in clk.inputs.values():
                    if inp is not None:
                        self.add_edge(graph, inp, clk)
            elif isinstance(clk, Clock) or isinstance(clk, Div):
                if clk.input is None:
                    continue
                self.add_edge(graph, clk.input, clk)
            else:
                raise NotImplementedError(f"Missing type {clk.__class__}")

        # find start / endpoints
        with graph.subgraph() as s:
            s.attr(rank="same")
            for n in self.clocks.get_input_clks():
                if self.filters.lookup_clock(n) is not None:
                    s.node(n.name)

        with graph.subgraph() as s:
            s.attr(rank="same")
            for n in self.clocks.get_output_clks():
                if self.filters.lookup_clock(n) is not None:
                    s.node(n.name)

        self.graph = graph

