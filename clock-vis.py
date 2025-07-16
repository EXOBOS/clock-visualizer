#!/usr/bin/env python3
from src.graphs import ClockGraph
from src.filters import FilterAccumulator, QueryFilter
from src.grapher import Grapher

with open('./socs/NXP_LPC55S1x_DS.yaml', 'r') as fp:
    clkgraph = ClockGraph.from_yaml(fp)

filter = QueryFilter(clkgraph, clkgraph.get_clk("clk_pll1"))
filters = FilterAccumulator()
filters.add_filter(filter)
#Grapher(clkgraph, filters)

