# 🕰️🕵️‍♀️ SOC Clock Visualizer

Most (if not all) SOCs / MCUs have some kind of relatively complex clock
subsystem. To configure these vendors often provide a graphic utility making it
easier to work with them. But what happens if you want to go the other way? You
have a known system, but want to take a look at the state of its clocks. To
fill the gap between staring to long at the SOCs user manual or simply giving
up, we created this tooling.

Provided somebody already wrote the clock description file for the SOCs and you
have a (partial) memory dump, one can easily take a look at the current state
of the systems clock circuit using graphing engines like [graphviz][graphviz].

> [!NOTE]
> For all currently supported socs take a look in [the socs](./socs/)
> subdirectory. To implement a new SOCs, take a look below.

## Usage

Currently, only intel hex memory dumps are supported.

```
usage: clock-vis.py [-h] -s SOC -o OUTPUT [-t TITLE] [-m MEMORYFILE] [-sc] [-q CLOCKNAME] [-sq]

Visualize the clock circuits configuration using register dump for an SOC of your choice.

options:
  -h, --help            show this help message and exit
  -s SOC, --soc SOC     Select the SOC. See ./socs/ for a list of all supported
  -o OUTPUT, --output OUTPUT
                        Output file name. Suffix is used to determine file type. Use .dot for graphviz
                        code
  -t TITLE, --title TITLE
                        Title / comment in the top left corner of the graph
  -m MEMORYFILE, --memory MEMORYFILE
                        Memory file containing the clock registers. Parser is determined by suffix.
  -sc, --only-show-config
                        By default the program will overlay the memory configuration over complete
                        graph. To only show the active edges and nodes, use this.
  -q CLOCKNAME, --query CLOCKNAME
                        Visualize the connections made by a single clock. If a memory dump is provided,
                        only active connections are traversed
  -sq, --only-show-query
                        Limit the graph to only show edges and nodes highlighted by the query.

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
```

## Getting the memory dump

For most MCUs this is fairly easy, assuming one has a debug connection.

```
(gdb) dump ihex memory /tmp/state.bin 0x50000000 0x50000FFC
```

> [!WARNING]
> If using PyOCD, accessing these memory regions can return an error like `Cannot
> access memory at address`. This is because GDB restricts memory accesses to
> the regions defined by the memory map. For PyOCD these do not include
> peripheral registers or other interesting regions. To disable this default
> behavior one can use
>
> ```
> (gdb) set mem inaccessible-by-default off
> ```

## Writing a new SOC clock description

The descriptions files are in the [socs subfolder](./socs/). During execution
the program will try to find the provided SOC name by looking for a `.yaml`
file with the same name. In order to create your own SOC, create a file with
the SOCs name and using the [NXP LPC55S1x file](./socs/NXP_LPC55S1x_DS.yaml) as
a reference, write down the information provided by the user manual.

The files are standard yaml syntax, so cross-links and references work as
defined by the standard. Note thoo, that additionally to the standard tags we
introduced a few of our own, namely:

- `!addr32le [ADDRESS, [BIT_START, BIT_END]]`: Describes the register bits entailing this value, using 32bit and little-endian registers
- `!!lambda ARG1, ARG2 -> FUNC`: A small lambda function for simple computations. Mostly used to describe mathematical formulas.
- `!add SEQUENCE`: Adds all integers in this sequence together. Use it to separate base address and register offset

One can verify the written description by running a json schema validator over
it using the schema provided by [the file
`soc.schema.json`](./socs/soc.schema.json). As an example YAMLLS directly
integrates this into the linter, but the program will also run a verification
during description loading and throw respective errors.

[graphviz]: https://graphviz.org/
