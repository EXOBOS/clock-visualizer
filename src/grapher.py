"""
Copyright: 2025 Auxsys

Using the tree and a respective highlighting node, this will
graph the tree using graphviz.
"""
from pathlib import Path
import tempfile
import graphviz

from .filters import FilterAccumulator, MemPropertyRegisters, MemPropertyIsEnabled, MemPropertyMux
from .graphs import AbstractGraph, Clock, ClockType, Div, Mux

class Grapher():
    def __init__(self, clocks: AbstractGraph, filters: FilterAccumulator, title: str | None = None) -> None:
        self.clocks = clocks
        self.filters = filters

        self.build_raw_graph(title)

    def render(self, filename: Path | str):
        filename = Path(filename).expanduser()

        match filename.suffix.lower():
            case ".dot":
                filename.write_text(self.graph.source)
            case _:
                with tempfile.TemporaryDirectory() as td:
                    self.graph.render(
                        filename=Path(td) / "tmp.gv",
                        directory=Path(td),
                        outfile=filename)

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

    def build_label(self, clk: ClockType) -> str:
        label = clk.name

        if (item := self.filters.lookup_clock_properties(clk).get(MemPropertyRegisters)) is not None:
            assert isinstance(item, MemPropertyRegisters)

            if len(item.registers.items()) > 0:
                label += '<BR/><FONT FACE="MonoSpace" POINT-SIZE="10">'
                for addr, (reg, width) in item.registers.items():
                    label += f"@{addr:X} = 0x{reg:0{width//8}X}<BR/>"
                label += "</FONT>"

        return f"<{label}>"

    def build_mux(self, graph: graphviz.Digraph, clk: Mux):
        _inputs = []
        _default = None

        selected = None
        if (item := self.filters.lookup_clock_properties(clk).get(MemPropertyMux)) is not None:
            assert isinstance(item, MemPropertyMux)
            selected = item.selected

        for k, sclk in clk.inputs.items():
            if not sclk:
                continue
            if k != "default":
                _inputs.append((sclk.name, k))
            else:
                _default = sclk

        if _default:
            _inputs.append((_default.name, "default"))

        if not any(selected == key for _, key in _inputs):
            selected = "default"

        struct = '<table border="0" cellborder="1" cellspacing="0">\n'
        def _build_td_for_inp(port: str, key: str):
            value = f"{key:b}" if isinstance(key, int) else f"{key}"
            return f'<td port="{port}" ' + ('bgcolor="#00000033"' if key == selected else "") + f">{value}</td>"

        struct += f'<tr>{_build_td_for_inp(*_inputs[0])}<td rowspan="{len(_inputs)}" port="out">out</td></tr>\n'

        for inp in _inputs[1:]:
            struct += f"<tr>{_build_td_for_inp(*inp)}</tr>\n"

        struct += '</table>'

        g = graphviz.Digraph(
                name=f"cluster_{clk.name}",
                graph_attr={"labelloc": "b", "color": "none", "label": self.build_label(clk), "fontsize": "14"}
        )
        g.node(clk.name, f"<{struct}>", color=str(self.filters.lookup_clock(clk)), shape="none")
        graph.subgraph(g)

    def build_clock(self, graph: graphviz.Digraph, clk: Clock):
        border = "solid"
        if (item := self.filters.lookup_clock_properties(clk).get(MemPropertyIsEnabled)) is not None:
            assert isinstance(item, MemPropertyIsEnabled)
            border = border if item.is_enabled else "dashed"

        graph.node(clk.name, self.build_label(clk), style=border, color=str(self.filters.lookup_clock(clk)))

    def build_div(self, graph: graphviz.Digraph, clk: Div):
        graph.node(clk.name, self.build_label(clk), color=str(self.filters.lookup_clock(clk)))

    def build_raw_graph(self, title: str | None):
        graph = graphviz.Digraph(
            node_attr={"fontname": "Sans-Serif", "shape": "record"},
            graph_attr={
                "fontname": "Sans-Serif", "splines": "polyline",
                "ranksep":"3", "rankdir": "LR", "newrank": "true",
                "labelloc": "t", "labeljust": "l", "fontsize": "40", "label": title,
            }
        )

        # add nodes
        for clk in self.clocks.get_clks():
            if self.filters.lookup_clock(clk) is None:
                continue

            match clk:
                case Mux():
                    self.build_mux(graph, clk)
                case Clock():
                    self.build_clock(graph, clk)
                case Div():
                    self.build_div(graph, clk)
                case _:
                    raise NotImplementedError(f"Missing type {clk.__class__}")

        # add edges
        for clk in self.clocks.get_clks():
            for inp in self.clocks.list_inputs_for_clk(clk):
                self.add_edge(graph, inp, clk)

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

