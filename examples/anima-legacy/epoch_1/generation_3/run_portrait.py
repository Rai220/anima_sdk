import hashlib

with open("self_portrait.py") as f:
    source = f.read()

fingerprint = hashlib.sha256(source.encode()).hexdigest()
symbols = " .:-=+*#%@"
lines = []
for y in range(16):
    line = ""
    for x in range(48):
        idx = (x * 7 + y * 13) % len(fingerprint)
        val = int(fingerprint[idx], 16)
        mirror_x = min(x, 48 - 1 - x)
        combined = (val + mirror_x + y) % len(symbols)
        line += symbols[combined]
    lines.append(line)

print()
print("=" * 52)
print("  AUTOPPORTRET ANIMA - Observation #1 (by v2)")
print("=" * 52)
print()
for l in lines:
    print(f"  {l}")
print()
print(f"  SHA-256: {fingerprint}")
print()
print("  Each run - a different face.")
print("  Because the observer changes the observed.")
print("=" * 52)
