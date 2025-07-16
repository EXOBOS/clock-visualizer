#!/usr/bin/env python3
from src.graphs import ClockGraph, MemoryClockGraph
from src.filters import FilterAccumulator, QueryFilter
from src.grapher import Grapher
from src.utils import SparseMemory

with open('./socs/NXP_LPC55S1x_DS.yaml', 'r') as fp:
    clkgraph = ClockGraph.from_yaml(fp)

memory = SparseMemory()
mem_graph = MemoryClockGraph(clkgraph, memory)

filter = QueryFilter(clkgraph, clkgraph.get_clk("clk_pll1"))
filters = FilterAccumulator()
filters.add_filter(filter)
#Grapher(clkgraph, filters)

