"""
Copyright: 2025 Auxsys

Testing for sparse memory class
"""
import unittest
import textwrap
import io
from src.utils.sparse_memory import SparseMemory

class TestSparseMemory(unittest.TestCase):
    def setUp(self):
        self.def_byte = bytes([0xFF])
        self.mem = SparseMemory(default_byte=self.def_byte[0])

    def test_setint(self):
        # set - test int index
        self.mem[0x10] = 5
        self.assertEqual(self.mem.get_raw(), self.def_byte * 0x10 + b"\x05")

    def test_setslice(self):
        # set - test slice index
        self.mem[7:10] = b"abc" # insert
        self.assertEqual(self.mem.get_raw(start_address=2), self.def_byte * 5 + b"abc")

        self.mem[2:5] = b"123" # insert
        self.assertEqual(self.mem.get_raw(start_address=2), b"123" + (self.def_byte * 2) + b"abc")

        self.mem[4:8] = b"----" # insert overlapping lr
        self.assertEqual(self.mem.get_raw(start_address=2), b"12----bc")

        self.mem[5:7] = b"00"  # insert overlapping single segment
        self.assertEqual(self.mem.get_raw(start_address=2), b"12-00-bc")

        self.mem[10:12] = b"--" ## append directly after
        self.assertEqual(self.mem.get_raw(start_address=2), b"12-00-bc--")

        self.mem[0:2] = b"--" ## append directly before
        self.assertEqual(self.mem.get_raw(start_address=0), b"--12-00-bc--")

    def test_getint(self):
        self.mem[0x10] = 5
        self.assertEqual(self.mem[0x10], 5)

        self.mem[2:20] = b"\x55" * 18
        self.assertEqual(self.mem[0x10], 0x55)

        self.assertEqual(self.mem[0], self.def_byte[0])

    def test_getslice(self):
        self.mem[5] = 5
        self.assertEqual(self.mem[4:6], self.def_byte + b"\x05")

        self.mem[4:8] = b"abcd"
        self.assertEqual(self.mem[5:7], b"bc")
        self.assertEqual(self.mem[3:9], self.def_byte + b"abcd" + self.def_byte)
        self.assertEqual(self.mem[0:5], self.def_byte * 4 + b"a")
        self.assertEqual(self.mem[7:10], b"d" + self.def_byte * 2)


    def test_intelhex(self):
        data = textwrap.dedent("""
            :02010000aabb98
            :02010200ccdd52
            :02010400eeff0c
            :00000001FF
        """)

        mem = SparseMemory.from_intelhex(io.StringIO(data))
        self.assertEqual(mem.get_raw(start_address=0x0100), bytes.fromhex("aabbccddeeff"))
