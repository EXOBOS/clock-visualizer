#!/usr/bin/env python3
from src.clkdesc import ClkDescription
from src.grapher import Grapher

with open('./socs/NXP_LPC55S1x_DS.yaml', 'r') as fp:
    clkdesc = ClkDescription.from_yaml(fp)

Grapher(clkdesc)
