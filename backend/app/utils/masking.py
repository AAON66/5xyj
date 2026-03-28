from __future__ import annotations

from typing import Optional


def mask_id_number(id_number: Optional[str]) -> Optional[str]:
    """Mask ID number to show first 3 and last 4 characters (per D-09).

    Returns the original value for None, empty strings, or strings shorter
    than 8 characters.  For 8+ character strings, the middle portion is
    replaced with asterisks.
    """
    if not id_number or len(id_number) < 8:
        return id_number
    return id_number[:3] + '*' * (len(id_number) - 7) + id_number[-4:]
