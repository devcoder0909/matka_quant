"""
Project Trinetra - Matka Math Utilities.

Domain-specific helpers for patti/ank/jodi validation and conversion.
"""

from __future__ import annotations

from typing import Dict, List


def patti_to_ank(patti: str) -> int:
    """
    Convert a 3-digit patti to its ank (single digit).

    The ank is the sum of the patti's digits modulo 10.

    Examples:
        patti_to_ank("234") -> (2+3+4) % 10 = 9
        patti_to_ank("550") -> (5+5+0) % 10 = 0

    Args:
        patti: 3-character string of digits (e.g. "234").

    Returns:
        Single digit 0-9.

    Raises:
        ValueError: If patti is not a valid 3-digit numeric string.
    """
    if not validate_patti(patti):
        raise ValueError(f"Invalid patti: {patti!r}. Must be a 3-digit numeric string.")
    return sum(int(d) for d in patti) % 10


def anks_to_jodi(open_ank: int, close_ank: int) -> str:
    """
    Combine open_ank and close_ank into a 2-digit jodi string.

    Args:
        open_ank: Single digit 0-9.
        close_ank: Single digit 0-9.

    Returns:
        2-character string, e.g. "05", "93".

    Raises:
        ValueError: If either ank is not in [0, 9].
    """
    if not (0 <= open_ank <= 9):
        raise ValueError(f"open_ank must be 0-9, got {open_ank}")
    if not (0 <= close_ank <= 9):
        raise ValueError(f"close_ank must be 0-9, got {close_ank}")
    return f"{open_ank}{close_ank}"


def validate_patti(patti: str) -> bool:
    """
    Check whether a string is a valid 3-digit patti.

    Valid patti: exactly 3 characters, all digits, numeric value 000-999.
    """
    if not isinstance(patti, str):
        return False
    if len(patti) != 3:
        return False
    return patti.isdigit()


def validate_jodi(jodi: str) -> bool:
    """
    Check whether a string is a valid 2-digit jodi.

    Valid jodi: exactly 2 characters, all digits, 00-99.
    """
    if not isinstance(jodi, str):
        return False
    if len(jodi) != 2:
        return False
    return jodi.isdigit()


def validate_ank(ank: int | str) -> bool:
    """
    Check whether a value is a valid single-digit ank (0-9).
    """
    try:
        val = int(ank)
        return 0 <= val <= 9
    except (TypeError, ValueError):
        return False


def validate_result_consistency(
    open_patti: str | None,
    open_ank: int | None,
    jodi: str | None,
    close_ank: int | None,
    close_patti: str | None,
) -> Dict[str, object]:
    """
    Validate internal consistency of a full result record.

    Checks:
    1. If open_patti is present, its digit-sum mod 10 must equal open_ank.
    2. If close_patti is present, its digit-sum mod 10 must equal close_ank.
    3. If both anks are present, their concatenation must equal jodi.
    4. Individual format validations for patti/ank/jodi.

    Returns:
        {
            "is_valid": bool,
            "errors": ["error description", ...]
        }
    """
    errors: List[str] = []

    # ── Format checks ─────────────────────────────────────────────────
    if open_patti is not None and not validate_patti(open_patti):
        errors.append(f"Invalid open_patti format: {open_patti!r}")

    if close_patti is not None and not validate_patti(close_patti):
        errors.append(f"Invalid close_patti format: {close_patti!r}")

    if jodi is not None and not validate_jodi(jodi):
        errors.append(f"Invalid jodi format: {jodi!r}")

    if open_ank is not None and not validate_ank(open_ank):
        errors.append(f"Invalid open_ank: {open_ank!r}")

    if close_ank is not None and not validate_ank(close_ank):
        errors.append(f"Invalid close_ank: {close_ank!r}")

    # ── Cross-field consistency ───────────────────────────────────────
    if open_patti is not None and validate_patti(open_patti) and open_ank is not None:
        expected_ank = patti_to_ank(open_patti)
        if int(open_ank) != expected_ank:
            errors.append(
                f"open_ank mismatch: patti {open_patti} should give ank "
                f"{expected_ank}, got {open_ank}"
            )

    if close_patti is not None and validate_patti(close_patti) and close_ank is not None:
        expected_ank = patti_to_ank(close_patti)
        if int(close_ank) != expected_ank:
            errors.append(
                f"close_ank mismatch: patti {close_patti} should give ank "
                f"{expected_ank}, got {close_ank}"
            )

    if (
        open_ank is not None
        and close_ank is not None
        and jodi is not None
        and validate_ank(open_ank)
        and validate_ank(close_ank)
        and validate_jodi(jodi)
    ):
        expected_jodi = anks_to_jodi(int(open_ank), int(close_ank))
        if jodi != expected_jodi:
            errors.append(
                f"jodi mismatch: open_ank={open_ank}, close_ank={close_ank} "
                f"should give jodi {expected_jodi}, got {jodi}"
            )

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
    }
