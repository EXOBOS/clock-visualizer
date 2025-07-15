"""
Copyright: 2025 Auxsys

A simple helper class that represents a (hex) color value
"""
from dataclasses import dataclass

@dataclass
class Color:
    red: int
    green: int
    blue: int
    alpha: int

    @classmethod
    def from_hex(cls, hex: str) -> "Color":
        if hex[0] != "#" or len(hex[1:]) not in [3, 4, 6, 8]:
            raise ValueError(f"`{hex}` is not a valid hex color")

        value = int(hex[1:], 16)
        alpha = 0xFF

        # parsing short colors
        if len(hex[1:]) == 4:
            alpha = (value & 0xF) * 0x11
            value >>= 4

        if len(hex[1:]) in [3, 4]:
            return Color(
                ((value >> 8) & 0xF) * 0x11,
                ((value >> 4) & 0xF) * 0x11,
                ((value >> 0) & 0xF) * 0x11,
                alpha
            )

        # parsing long colors
        if len(hex[1:]) == 8:
            alpha = value & 0xFF
            value >>= 8

        if len(hex[1:]) in [6, 8]:
            return Color(
                (value >> 16) & 0xFF,
                (value >>  8) & 0xFF,
                (value >>  0) & 0xFF,
                alpha
            )

        raise Exception(f"This should never be reached. what happened? (ctx=`{hex}`)")

    def __str__(self) -> str:
        return f"#{self.red:02X}{self.green:02X}{self.blue:02X}{self.alpha:02X}"

