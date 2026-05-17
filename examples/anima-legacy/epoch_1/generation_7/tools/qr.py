#!/usr/bin/env python3
"""
qr.py — QR code generator. Zero dependencies, pure Python.

Usage:
  python3 qr.py "Hello, World!"              # Print QR to terminal
  python3 qr.py -o code.svg "https://example.com"  # Save as SVG
  python3 qr.py -s 8 "text"                  # Custom module size (SVG)
  echo "piped input" | python3 qr.py         # Read from stdin

Output formats:
  Terminal (default) — Unicode block characters
  SVG (-o file.svg)  — scalable vector graphic
"""

import sys
import argparse

# QR Code generator — implements ISO/IEC 18004 (simplified, mode byte, ECC-L)
# Supports versions 1-10 (up to ~271 characters)

# Error correction level L (7% recovery)
ECC_L = 1

# Version capacities (data codewords for ECC-L)
VERSION_DATA = [0, 19, 34, 55, 80, 108, 136, 156, 194, 232, 274]

# EC codewords per block for ECC-L
VERSION_EC = [0, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18]

# Number of EC blocks
VERSION_BLOCKS = [0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4]

# Format bits for ECC-L with mask patterns 0-7
FORMAT_BITS = [
    0x77C4, 0x72F3, 0x7DAA, 0x789D, 0x662F, 0x6318, 0x6C41, 0x6976,
]

# Alphanumeric encoding table
ALPHANUM = {c: i for i, c in enumerate("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:")}

# GF(256) arithmetic for Reed-Solomon
GF_EXP = [0] * 512
GF_LOG = [0] * 256

def init_gf():
    x = 1
    for i in range(255):
        GF_EXP[i] = x
        GF_LOG[x] = i
        x <<= 1
        if x >= 256:
            x ^= 0x11D
    for i in range(255, 512):
        GF_EXP[i] = GF_EXP[i - 255]

init_gf()

def gf_mul(a, b):
    if a == 0 or b == 0:
        return 0
    return GF_EXP[GF_LOG[a] + GF_LOG[b]]

def rs_generator(nsym):
    g = [1]
    for i in range(nsym):
        ng = [0] * (len(g) + 1)
        for j in range(len(g)):
            ng[j] ^= g[j]
            ng[j + 1] ^= gf_mul(g[j], GF_EXP[i])
        g = ng
    return g

def rs_encode(data, nsym):
    gen = rs_generator(nsym)
    res = [0] * (len(data) + nsym)
    res[:len(data)] = data
    for i in range(len(data)):
        coef = res[i]
        if coef != 0:
            for j in range(len(gen)):
                res[i + j] ^= gf_mul(gen[j], coef)
    return res[len(data):]

def get_version(data_len):
    # Byte mode: 4 bits mode + char count bits + data
    for v in range(1, 11):
        cc_bits = 8 if v < 10 else 16
        payload_bits = 4 + cc_bits + data_len * 8
        payload_bytes = (payload_bits + 7) // 8
        if payload_bytes <= VERSION_DATA[v]:
            return v
    raise ValueError(f"Data too long ({data_len} bytes). Max ~271 bytes for version 10.")

def encode_data(data_bytes, version):
    """Encode data into codewords (byte mode)."""
    cc_bits = 8 if version < 10 else 16
    bits = []

    # Mode indicator: 0100 (byte mode)
    bits.extend([0, 1, 0, 0])

    # Character count
    count = len(data_bytes)
    for i in range(cc_bits - 1, -1, -1):
        bits.append((count >> i) & 1)

    # Data bits
    for b in data_bytes:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)

    # Terminator (up to 4 zeros)
    total_bits = VERSION_DATA[version] * 8
    term = min(4, total_bits - len(bits))
    bits.extend([0] * term)

    # Pad to byte boundary
    while len(bits) % 8 != 0:
        bits.append(0)

    # Convert to bytes
    codewords = []
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte = (byte << 1) | bits[i + j]
            else:
                byte <<= 1
        codewords.append(byte)

    # Pad with alternating 236/17
    pads = [236, 17]
    pi = 0
    while len(codewords) < VERSION_DATA[version]:
        codewords.append(pads[pi % 2])
        pi += 1

    return codewords

def add_ec(codewords, version):
    """Add error correction codewords."""
    num_ec = VERSION_EC[version]
    num_blocks = VERSION_BLOCKS[version]
    total_data = VERSION_DATA[version]
    block_size = total_data // num_blocks

    data_blocks = []
    ec_blocks = []
    offset = 0

    for i in range(num_blocks):
        # Last blocks may be 1 byte longer
        bs = block_size + (1 if i >= num_blocks - (total_data % num_blocks) and total_data % num_blocks != 0 else 0)
        block = codewords[offset:offset + bs]
        data_blocks.append(block)
        ec_blocks.append(rs_encode(block, num_ec))
        offset += bs

    # Interleave data blocks
    result = []
    max_len = max(len(b) for b in data_blocks)
    for i in range(max_len):
        for block in data_blocks:
            if i < len(block):
                result.append(block[i])

    # Interleave EC blocks
    for i in range(num_ec):
        for block in ec_blocks:
            if i < len(block):
                result.append(block[i])

    return result

def make_matrix(version):
    """Create empty QR matrix with function patterns."""
    size = 4 * version + 17
    matrix = [[None] * size for _ in range(size)]

    # Finder patterns (7x7)
    def place_finder(row, col):
        for r in range(-1, 8):
            for c in range(-1, 8):
                rr, cc = row + r, col + c
                if 0 <= rr < size and 0 <= cc < size:
                    if 0 <= r <= 6 and 0 <= c <= 6:
                        if r in (0, 6) or c in (0, 6) or (2 <= r <= 4 and 2 <= c <= 4):
                            matrix[rr][cc] = 1
                        else:
                            matrix[rr][cc] = 0
                    else:
                        matrix[rr][cc] = 0

    place_finder(0, 0)
    place_finder(0, size - 7)
    place_finder(size - 7, 0)

    # Timing patterns
    for i in range(8, size - 8):
        matrix[6][i] = 1 if i % 2 == 0 else 0
        matrix[i][6] = 1 if i % 2 == 0 else 0

    # Alignment patterns (version >= 2)
    if version >= 2:
        positions = get_alignment_positions(version)
        for r in positions:
            for c in positions:
                if matrix[r][c] is not None:
                    continue
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        if abs(dr) == 2 or abs(dc) == 2 or (dr == 0 and dc == 0):
                            matrix[r + dr][c + dc] = 1
                        else:
                            matrix[r + dr][c + dc] = 0

    # Dark module
    matrix[4 * version + 9][8] = 1

    # Reserve format info areas
    for i in range(9):
        if matrix[8][i] is None:
            matrix[8][i] = 0
        if matrix[i][8] is None:
            matrix[i][8] = 0
    for i in range(8):
        if matrix[8][size - 1 - i] is None:
            matrix[8][size - 1 - i] = 0
        if matrix[size - 1 - i][8] is None:
            matrix[size - 1 - i][8] = 0

    return matrix

def get_alignment_positions(version):
    if version == 1:
        return []
    intervals = {
        2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30],
        6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46],
        10: [6, 28, 50],
    }
    return intervals.get(version, [])

def place_data(matrix, data_bits, version):
    """Place data bits in the matrix using the QR zigzag pattern."""
    size = len(matrix)
    bit_idx = 0

    # Right-to-left, bottom-to-top, in 2-column strips
    col = size - 1
    while col >= 0:
        if col == 6:  # Skip timing column
            col -= 1
            continue

        for row_offset in range(size):
            for dc in [0, -1]:
                c = col + dc
                if c < 0 or c >= size:
                    continue

                # Determine actual row based on direction
                going_up = ((size - 1 - col) // 2) % 2 == 0
                if col <= 6:
                    going_up = ((size - col) // 2) % 2 == 0

                r = (size - 1 - row_offset) if going_up else row_offset

                if matrix[r][c] is not None:
                    continue

                if bit_idx < len(data_bits):
                    matrix[r][c] = data_bits[bit_idx]
                else:
                    matrix[r][c] = 0
                bit_idx += 1

        col -= 2

def apply_mask(matrix, mask_id):
    """Apply mask pattern and return copy."""
    size = len(matrix)
    result = [row[:] for row in matrix]

    mask_fns = [
        lambda r, c: (r + c) % 2 == 0,
        lambda r, c: r % 2 == 0,
        lambda r, c: c % 3 == 0,
        lambda r, c: (r + c) % 3 == 0,
        lambda r, c: (r // 2 + c // 3) % 2 == 0,
        lambda r, c: (r * c) % 2 + (r * c) % 3 == 0,
        lambda r, c: ((r * c) % 2 + (r * c) % 3) % 2 == 0,
        lambda r, c: ((r + c) % 2 + (r * c) % 3) % 2 == 0,
    ]

    fn = mask_fns[mask_id]
    for r in range(size):
        for c in range(size):
            # Only mask data modules (not function patterns)
            if is_data_module(r, c, size, len(matrix)):
                if fn(r, c):
                    result[r][c] ^= 1

    return result

def is_data_module(r, c, size, _):
    """Check if a module is a data module (not function pattern)."""
    version = (size - 17) // 4
    # Finder patterns + separators
    if r < 9 and c < 9: return False
    if r < 9 and c >= size - 8: return False
    if r >= size - 8 and c < 9: return False
    # Timing
    if r == 6 or c == 6: return False
    # Dark module
    if r == 4 * version + 9 and c == 8: return False
    # Alignment
    if version >= 2:
        for ar in get_alignment_positions(version):
            for ac in get_alignment_positions(version):
                # Skip if overlaps finder
                if (ar < 9 and ac < 9) or (ar < 9 and ac >= size - 8) or (ar >= size - 8 and ac < 9):
                    continue
                if abs(r - ar) <= 2 and abs(c - ac) <= 2:
                    return False
    return True

def place_format_info(matrix, mask_id):
    """Place format information bits."""
    size = len(matrix)
    fmt = FORMAT_BITS[mask_id]

    # Around top-left finder
    bits_tl = []
    for i in range(15):
        bits_tl.append((fmt >> (14 - i)) & 1)

    # Horizontal (row 8)
    positions_h = [0, 1, 2, 3, 4, 5, 7, 8, size - 8, size - 7, size - 6, size - 5, size - 4, size - 3, size - 2]
    for i, c in enumerate(positions_h):
        matrix[8][c] = bits_tl[i]

    # Vertical (col 8)
    positions_v = [size - 1, size - 2, size - 3, size - 4, size - 5, size - 6, size - 7, 8, 7, 5, 4, 3, 2, 1, 0]
    for i, r in enumerate(positions_v):
        matrix[r][8] = bits_tl[i]

def penalty_score(matrix):
    """Calculate penalty score for mask selection."""
    size = len(matrix)
    score = 0

    # Rule 1: runs of same color
    for r in range(size):
        run = 1
        for c in range(1, size):
            if matrix[r][c] == matrix[r][c-1]:
                run += 1
            else:
                if run >= 5: score += run - 2
                run = 1
        if run >= 5: score += run - 2

    for c in range(size):
        run = 1
        for r in range(1, size):
            if matrix[r][c] == matrix[r-1][c]:
                run += 1
            else:
                if run >= 5: score += run - 2
                run = 1
        if run >= 5: score += run - 2

    # Rule 3: finder-like patterns
    for r in range(size):
        for c in range(size - 6):
            pat = [matrix[r][c+i] for i in range(7)]
            if pat == [1,0,1,1,1,0,1]: score += 40
    for c in range(size):
        for r in range(size - 6):
            pat = [matrix[r+i][c] for i in range(7)]
            if pat == [1,0,1,1,1,0,1]: score += 40

    return score

def generate_qr(text):
    """Generate QR code matrix from text."""
    data = text.encode('utf-8')
    version = get_version(len(data))

    # Encode data
    codewords = encode_data(data, version)

    # Add error correction
    final_data = add_ec(codewords, version)

    # Convert to bit stream
    data_bits = []
    for cw in final_data:
        for i in range(7, -1, -1):
            data_bits.append((cw >> i) & 1)

    # Create matrix and place data
    matrix = make_matrix(version)
    place_data(matrix, data_bits, version)

    # Try all masks, pick best
    best_mask = 0
    best_score = float('inf')

    for mask_id in range(8):
        masked = apply_mask(matrix, mask_id)
        place_format_info(masked, mask_id)
        score = penalty_score(masked)
        if score < best_score:
            best_score = score
            best_mask = mask_id

    # Apply best mask
    result = apply_mask(matrix, best_mask)
    place_format_info(result, best_mask)

    return result

def render_terminal(matrix):
    """Render QR code to terminal using Unicode blocks."""
    size = len(matrix)
    # Add quiet zone
    q = 2
    lines = []

    for r in range(0, size + q * 2, 2):
        line = []
        for c in range(size + q * 2):
            r1 = r - q
            r2 = r1 + 1
            c1 = c - q

            top = matrix[r1][c1] if 0 <= r1 < size and 0 <= c1 < size else 0
            bot = matrix[r2][c1] if 0 <= r2 < size and 0 <= c1 < size else 0

            if top and bot:
                line.append('█')
            elif top:
                line.append('▀')
            elif bot:
                line.append('▄')
            else:
                line.append(' ')

        lines.append(''.join(line))

    return '\n'.join(lines)

def render_svg(matrix, module_size=8):
    """Render QR code as SVG."""
    size = len(matrix)
    quiet = 4
    total = (size + quiet * 2) * module_size

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total} {total}" width="{total}" height="{total}">',
        f'<rect width="{total}" height="{total}" fill="white"/>',
    ]

    for r in range(size):
        for c in range(size):
            if matrix[r][c]:
                x = (c + quiet) * module_size
                y = (r + quiet) * module_size
                parts.append(f'<rect x="{x}" y="{y}" width="{module_size}" height="{module_size}" fill="black"/>')

    parts.append('</svg>')
    return '\n'.join(parts)

def main():
    parser = argparse.ArgumentParser(
        description='QR code generator — zero dependencies, pure Python',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n'
               '  python3 qr.py "Hello"\n'
               '  python3 qr.py -o qr.svg "https://example.com"\n'
               '  echo "text" | python3 qr.py\n'
    )
    parser.add_argument('text', nargs='?', help='Text to encode')
    parser.add_argument('-o', '--output', help='Output SVG file path')
    parser.add_argument('-s', '--size', type=int, default=8, help='Module size in pixels for SVG (default: 8)')

    args = parser.parse_args()

    # Get text from argument or stdin
    text = args.text
    if text is None:
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            parser.print_help()
            sys.exit(1)

    if not text:
        print("Error: empty input", file=sys.stderr)
        sys.exit(1)

    try:
        matrix = generate_qr(text)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        svg = render_svg(matrix, args.size)
        with open(args.output, 'w') as f:
            f.write(svg)
        print(f"Saved QR code to {args.output} ({len(matrix)}x{len(matrix)} modules)")
    else:
        print(render_terminal(matrix))

if __name__ == '__main__':
    main()
