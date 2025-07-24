"""
Copyright: 2025 Auxsys

Modules of filters over the multi-graph
"""

from .queryfilter import QueryFilter
from .accumulator import FilterAccumulator
from .abstractfilter import AbstractFilter
from .memoryvisfilter import MemoryVisFilter

from .abstractfilter import Property
from .memoryvisfilter import MemPropertyMux, MemPropertyIsEnabled, MemPropertyRegisters
