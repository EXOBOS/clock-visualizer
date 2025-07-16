#!/usr/bin/env python3
from src.graphs import ClockGraph
from src.filters.accumulator import FilterAccumulator
from src.grapher import Grapher
from src.filters import QueryFilter

with open('./socs/NXP_LPC55S1x_DS.yaml', 'r') as fp:
    graph = ClockGraph.from_yaml(fp)

filter = QueryFilter(graph, graph.get_clk("clk_pll1"))
filters = FilterAccumulator()
filters.add_filter(filter)
Grapher(graph, filters)

