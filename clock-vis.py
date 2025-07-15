#!/usr/bin/env python3
from src.clkdesc import ClkDescription
from src.filters.accumulator import FilterAccumulator
from src.grapher import Grapher
from src.filters import QueryFilter

import sys

with open('./socs/NXP_LPC55S1x_DS.yaml', 'r') as fp:
    clkdesc = ClkDescription.from_yaml(fp)

filter = QueryFilter(clkdesc, clkdesc.get_clk("clk_pll1"))
filters = FilterAccumulator()
filters.add_filter(filter)
Grapher(clkdesc, filters)

