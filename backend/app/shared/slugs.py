"""Turning names into URL-safe, unique keys.

Used wherever a human-typed name needs a stable key: category and product
slugs ("Phones & Tablets" → "phones-tablets"), attribute codes
("Storage Size" → "storage_size").
"""

import re


def slugify(text: str, *, separator: str = "-", max_length: int) -> str:
    """Lowercase letters and digits joined by `separator`. Letters of any
    alphabet are kept; everything else is dropped. May return "" (for
    example for "???"), so callers supply a fallback."""
    words = re.findall(r"[^\W_]+", text.lower())
    return separator.join(words)[:max_length].strip(separator)


def unique_among(base: str, taken: set[str], *, separator: str = "-") -> str:
    """`base` if it is free, otherwise `base-2`, `base-3`, …"""
    if base not in taken:
        return base
    number = 2
    while f"{base}{separator}{number}" in taken:
        number += 1
    return f"{base}{separator}{number}"
