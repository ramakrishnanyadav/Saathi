"""Generate crisp standalone PWA icons using standard library struct and zlib."""

from __future__ import annotations

import os
import struct
import zlib


def create_png(width: int, height: int, r: int, g: int, b: int, filename: str) -> None:
    # Minimal valid PNG generator
    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))

    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0)  # filter type 0
        for x in range(width):
            # Draw rounded center accent icon
            cx, cy = width // 2, height // 2
            dist_sq = (x - cx) ** 2 + (y - cy) ** 2
            radius_sq = (width // 2 - 10) ** 2
            inner_radius_sq = (width // 4) ** 2

            if dist_sq < inner_radius_sq:
                # Amber warm center (#F59E0B)
                raw_data.extend([245, 158, 11])
            elif dist_sq < radius_sq:
                # Deep slate circle (#1E293B)
                raw_data.extend([30, 41, 59])
            else:
                # Dark obsidian background (#0D1117)
                raw_data.extend([13, 17, 23])

    idat = chunk(b"IDAT", zlib.compress(bytes(raw_data)))
    iend = chunk(b"IEND", b"")

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        f.write(header + ihdr + idat + iend)
    print(f"Generated icon: {filename}")


if __name__ == "__main__":
    create_png(192, 192, 245, 158, 11, "web/public/icon-192.png")
    create_png(512, 512, 245, 158, 11, "web/public/icon-512.png")
