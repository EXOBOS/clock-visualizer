#!/usr/bin/env python3
"""
Copyright: 2025 Auxsys

Using the tree and a respective highlighting node, this will
graph the tree using graphviz.
"""
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from textwrap import dedent
from pathlib import Path
from os import PathLike
import traceback
import sys

from src.graphs import ClockGraph, MemoryClockGraph
from src.filters import FilterAccumulator, QueryFilter, MemoryVisFilter
from src.grapher import Grapher
from src.utils import SparseMemory
from src.utils.sparse_memory import ParsingError, UnknownFiletypeError


SOC_DIR = Path("./socs/")


def parse():
    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        description="Visualize the clock circuits configuration using register dump for an SOC of your choice.",
        epilog=dedent(
            """\
            Most SOC vendors do not provide a tool to visualize the current state of their
            clock subsystem as it is right now on the chip. This is what this tool is for.

            Either visualize the current circuit without any configuarition loaded (e.g. to
            determine what should be set), or give it a dump of the relevant memory and the
            program will visualize the current clock network as described by the registers.

            Assuming the NXP LPC55S1x here, one can simply dump the relevant memory in
            intel hex format from within gdb with

              (gdb) dump ihex memory /tmp/state.bin 0x50000000 0x50000FFC

            If using PyOCD, one should first disable the default behavior of (for GDB)
            unknown memory being inaccessible with

              (gdb) set mem inaccessible-by-default off

            To write new SOC clock description files, see the readme.
        """
        ),
    )

    parser.add_argument(
        "-s",
        "--soc",
        help="Select the SOC. See ./socs/ for a list of all supported",
        required=True,
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output file name. Suffix is used to determine file type. Use .dot for graphviz code",
        required=True,
    )

    parser.add_argument(
        "-t",
        "--title",
        help="Title / comment in the top left corner of the graph",
        default=None,
    )

    parser.add_argument(
        "-m",
        "--memory",
        metavar="MEMORYFILE",
        default=None,
        help="Memory file containing the clock registers. Parser is determined by suffix.",
    )

    parser.add_argument(
        "-sc",
        "--only-show-config",
        action="store_true",
        help="By default the program will overlay the memory configuration over complete graph. To only show the active edges and nodes, use this.",
    )

    parser.add_argument(
        "-q",
        "--query",
        metavar="CLOCKNAME",
        default=None,
        help="Visualize the connections made by a single clock. If a memory dump is provided, only active connections are traversed",
    )

    parser.add_argument(
        "-sq",
        "--only-show-query",
        action="store_true",
        help="Limit the graph to only show edges and nodes highlighted by the query.",
    )

    return parser.parse_args()


def printe(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def main(
    *,
    soc: str,
    output_file: str,
    graph_title: str | None,
    memory_file: PathLike | str | None,
    query: str | None,
    only_show_config: bool = False,
    only_show_query: bool = False,
):

    # verify soc
    soc_file = SOC_DIR / f"{soc}.yaml"
    if not soc_file.is_file():
        printe(f"Unknown soc file ({soc_file}) was provided. Please use one of:")
        for soc_p in SOC_DIR.glob("*.yaml"):
            printe(f" - {soc_p.stem}")
        sys.exit(-1)

    with soc_file.open("r") as fp:
        main_graph = ClockGraph.from_yaml(fp)

    # load memory file
    mem_graph = None
    if memory_file:
        memory_file = Path(memory_file)
        if not memory_file.is_file():
            printe(
                f"Provided memory file ({memory_file}) is not a file or does not exist."
            )
            sys.exit(-1)
        try:
            memory = SparseMemory.parse_file(memory_file)
        except ParsingError as e:
            printe(
                f"Provided memory file ({memory_file}) could not be parsed due to an exception."
            )
            traceback.print_exception(e, file=sys.stderr)
            sys.exit(-1)
        except UnknownFiletypeError as e:
            printe(
                f"Parser not found for file ({memory_file}). Currently only supported are:"
            )
            for suffix, name in e.supported.items():
                printe(f" - `{suffix}`: {name}")
            sys.exit(-1)

        mem_graph = MemoryClockGraph(main_graph, memory)

    filters = FilterAccumulator(show_hidden=not only_show_query)

    # lookup our query
    if query is not None:
        queryclk = main_graph.get_clk(query)
        if queryclk is None:
            printe(f"Unknown clock {query}. Exiting...")
            sys.exit(-1)

        if mem_graph is None:
            qfilter = QueryFilter(main_graph, queryclk)
        else:
            qfilter = QueryFilter(mem_graph, queryclk)

        filters.add_filter(qfilter)

    if mem_graph is not None:
        filters.add_filter(MemoryVisFilter(mem_graph))

    g = Grapher(
        mem_graph if mem_graph is not None and only_show_config else main_graph,
        filters,
        graph_title,
    )

    g.render(output_file)


if __name__ == "__main__":
    args = parse()
    main(
        soc=args.soc,
        output_file=args.output,
        graph_title=args.title,
        memory_file=args.memory,
        query=args.query,
        only_show_config=args.only_show_config,
        only_show_query=args.only_show_query,
    )
