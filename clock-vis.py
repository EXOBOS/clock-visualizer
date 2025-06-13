#!/usr/bin/env python3
from src.clkdesc import ClkDescription

with open('./socs/NXP_LPC55S1x_DS.yaml', 'r') as fp:
    data = ClkDescription.from_yaml(fp)
