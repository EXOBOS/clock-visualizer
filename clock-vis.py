#!/usr/bin/env python3
from src.graphs import ClockGraph, MemoryClockGraph
from src.filters import FilterAccumulator, QueryFilter, MemoryVisFilter
from src.grapher import Grapher
from src.utils import SparseMemory

with open('./socs/NXP_LPC55S1x_DS.yaml', 'r') as fp:
    clkgraph = ClockGraph.from_yaml(fp)

#memory = SparseMemory()
with open("./tmp/stm32-syscon.bin", "r") as fp:
    memory = SparseMemory.from_intelhex(fp)
mem_graph = MemoryClockGraph(clkgraph, memory)

qfilter = QueryFilter(mem_graph, clkgraph.get_clk("clk_flexcomm6"))
mfilter = MemoryVisFilter(mem_graph)
filters = FilterAccumulator()
filters.add_filter(qfilter)
filters.add_filter(mfilter)
Grapher(clkgraph, filters)

