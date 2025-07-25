"""
Copyright: 2025 Auxsys

Class that handles reading and working on sparse memory. Used to
represent device memory containing the clock registers.
"""
from functools import total_ordering
from typing import IO, overload
from dataclasses import dataclass

from ..graphs.yamlobjects import AddrObject

@total_ordering
@dataclass(frozen=True)
class Segment:
    start: int
    stop: int

    def __lt__(self, other):
        return (self.start, self.stop) < (other.start, other.stop)

    @property
    def length(self):
        return self.stop - self.start

    def __contains__(self, item) -> bool:
        if isinstance(item, int):

            return self.start <= item and item < self.stop
        return False


class SparseMemory:
    def __init__(self, default_byte: int = 0x00) -> None:
        self._default_byte = default_byte

        self._segments: dict[Segment, bytearray] = {}

    def _cleanup_segments(self):
        cur_data: None | bytearray = None
        cur_segs: list = []
        for seg in [*sorted(self._segments.keys()), None]:
            if len(cur_segs) > 0 and seg is not None and cur_segs[-1].stop == seg.start:
                cur_segs.append(seg)
                assert cur_data is not None, "Yeah this should never be the case"
                cur_data += self._segments[seg]
            else:
                if len(cur_segs) > 1:
                    for cur_seg in cur_segs:
                        del self._segments[cur_seg]
                    assert cur_data is not None, "Yeah this should never be the case"
                    self._segments[Segment(cur_segs[0].start, cur_segs[-1].stop)] = cur_data

                if seg is None:
                    break

                cur_segs = [seg]
                cur_data = self._segments[seg].copy()

    @overload
    def __getitem__(self, key: int) -> int:
        ...

    @overload
    def __getitem__(self, key: slice) -> bytes:
        ...

    def __getitem__(self, key: int | slice) -> int | bytes:
        if isinstance(key, int):
            for seg in self._segments.keys():
                if key in seg:
                    return self._segments[seg][key - seg.start]
            return self._default_byte
        elif isinstance(key, slice):
            if not (key.step == 1 or key.step is None):
                raise KeyError("Only stepsize of 1 supported for slice")
            if key.stop is None or key.start is None:
                raise KeyError("Open slices are not supported")

            data = bytearray([self._default_byte]) * (key.stop - key.start)

            for seg in self._segments.keys():
                if seg.start <= key.start and key.stop <= seg.stop:
                    # -0[00]0-
                    data = self._segments[seg][key.start - seg.start:key.stop - seg.start]
                elif key.start <= seg.start and seg.stop <= key.stop:
                    # [-0000-]
                    data[seg.start - key.start:seg.stop - key.start] = self._segments[seg]
                elif key.start <= seg.start and seg.start <= key.stop:
                    # [-00]00-
                    data[seg.start - key.start:] = self._segments[seg][:key.stop - seg.start]
                elif key.start <= seg.stop and seg.stop <= key.stop:
                    # -00[00-]
                    data[:seg.stop - key.start] = self._segments[seg][key.start - seg.start:]

            return data
        else:
            raise KeyError(f"Only int and slice supported")

    @overload
    def __setitem__(self, key: int, value: int):
        ...

    @overload
    def __setitem__(self, key: slice, value: bytes):
        ...

    def __setitem__(self, key: int | slice, value: int | bytes):
        if isinstance(key, int):
            if not isinstance(value, int):
                raise ValueError("value is not of type int")

            for seg in self._segments.keys():
                if key in seg:
                    self._segments[seg][key - seg.start] = value
                    return

            self._segments[Segment(key, key + 1)] = bytearray([value])
        elif isinstance(key, slice):
            if not isinstance(value, bytes) and not isinstance(value, bytearray):
                raise KeyError("value is not of type bytes / bytearray")
            if not (key.step == 1 or key.step is None):
                raise KeyError("Only stepsize of 1 supported for slice")
            if key.stop is None or key.start is None:
                raise KeyError("Open slices are not supported")
            if key.stop - key.start != len(value):
                raise ValueError(f"len(value) != len(key) (got {len(value)} == {key.stop - key.start})")

            # remove previous segments that would overlap
            for seg in list(self._segments.keys()):
                ovalue = self._segments[seg]
                if seg.start <= key.start and key.stop <= seg.stop:
                    # -0[00]0-
                    del self._segments[seg]
                    self._segments[Segment(seg.start, key.start)] = ovalue[:key.start - seg.start]
                    self._segments[Segment(key.stop, seg.stop)] = ovalue[-(seg.stop - key.stop):]
                elif key.start <= seg.start and seg.stop <= key.stop:
                    # [-0000-]
                    del self._segments[seg]
                elif key.start <= seg.start and seg.start < key.stop:
                    # [-00]00-
                    del self._segments[seg]
                    self._segments[Segment(key.stop, seg.stop)] = ovalue[key.stop - seg.start:]
                elif key.start < seg.stop and seg.stop <= key.stop:
                    # -00[00-]
                    del self._segments[seg]
                    self._segments[Segment(seg.start, key.start)] = ovalue[:key.start - seg.stop]

            # insert our new segment
            self._segments[Segment(key.start, key.stop)] = bytearray(value)
        else:
            raise KeyError(f"Only int and slice supported")

        self._cleanup_segments()

    def get_register(self, addr: AddrObject) -> int:
        try:
            register = self[addr.addr:addr.addr + addr.width // 8]
            assert addr.endianess.value is not None
            value = int.from_bytes(register, addr.endianess.value, signed=False)

            if len(addr.bit) == 1:
                return (value >> addr.bit[0]) & 0x1
            else:
                map = ~(~1 << addr.bit[0]) & (~0 << addr.bit[1])
                return (value & map) >> addr.bit[1]
        except Exception as e:
            raise ValueError(f"Error trying to read register with {addr}", e)

    def get_raw(self, start_address: int = 0) -> bytes:
        data = b""

        for key in sorted(self._segments.keys()):
            if key.stop < start_address:
                continue

            cur_addr = start_address + len(data)
            assert key.start >= cur_addr, f"There seem to be overlapping segments"
            data += bytes([self._default_byte]) * (key.start - cur_addr)  # filling offset
            assert len(v := self._segments[key]) == key.length, f"data len({v}) seems to be different than what is defined in key {key}"
            data += self._segments[key]  # add our data

        return data

    @classmethod
    def from_intelhex(cls, indata: IO[str]) -> "SparseMemory":
        """
        Create parse memory from Intel Hex format
        """
        record_n, record = 0, ""
        data = indata.read()
        memory = SparseMemory()

        try:
            base_address = 0
            while ":" in data:
                record_n += 1
                _, record = data.split(":", maxsplit=1)

                byte_count = int(record[0:2], 16)
                data = record[8 + byte_count * 2 + 2:]
                record = record[:8 + byte_count * 2 + 2]

                address = int(record[2:6], 16)
                record_type = int(record[6:8], 16)
                chk = int(record[-2:], 16)

                # check checksum
                if sum(bytes.fromhex(record)) & 0xFF != 0:
                    raise Exception(f"Invalid Checksum - found 0x{chk:02X}")

                match record_type:
                    case 0:  # Data
                        bdata = bytes.fromhex(record[8:8 + byte_count * 2])
                        memory[base_address + address:base_address + address + byte_count] = bdata
                    case 1:  # End Of File
                        if byte_count != 0:
                            raise ValueError(f"type=0x1 [EOF], byte_count!=0 (got {byte_count})")
                        break
                    case 2 | 4:  # Extended Segment Address / Extended Linear Addr
                        if byte_count != 2:
                            raise ValueError(f"type=0x2, byte_count!=2 (got {byte_count})")

                        base_address = int(record[8:8 + 4], 16) << (4 if record_type == 2 else 16)
                    case _:
                        print(f"Ignoring record with type=`{record_type}`")

            return memory
        except Exception as e:
            raise ValueError(f"Couldn't process record {record_n} / `{record}`", e)
