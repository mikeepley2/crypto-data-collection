#!/usr/bin/env python3

import re

with open('/app/main.py') as f:
    content = f.read()

# Find all lines that mention volume processing
lines = content.split('\n')
print("=== Volume Processing Analysis ===")

volume_patterns = [
    r'total_volume',
    r'volume.*get\(',
    r'volume.*=.*0',
    r'volume.*append',
    r'volume.*\[',
    r'price_info\[.*volume',
]

for pattern in volume_patterns:
    print(f"\nPattern: {pattern}")
    for i, line in enumerate(lines):
        if re.search(pattern, line, re.IGNORECASE):
            print(f"  {i+1:3d}: {line.strip()}")

print("\n=== CoinGecko API call analysis ===")
for i, line in enumerate(lines):
    if 'coingecko.com' in line.lower() or 'get_price' in line:
        start = max(0, i-2)
        end = min(len(lines), i+3)
        print(f"\nContext around line {i+1}:")
        for j in range(start, end):
            prefix = ">>>" if j == i else "   "
            print(f"{prefix} {j+1:3d}: {lines[j]}")