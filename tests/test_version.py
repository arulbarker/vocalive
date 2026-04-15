import re
import pytest

pytestmark = pytest.mark.unit

import version


def test_version_format():
    """VERSION must be X.Y.Z semver (3 parts, all digits)."""
    parts = version.VERSION.split(".")
    assert len(parts) == 3, f"VERSION must have 3 parts, got {len(parts)}: {version.VERSION!r}"
    for part in parts:
        assert part.isdigit(), f"Each part must be all digits, got {part!r} in {version.VERSION!r}"


def test_version_parts_match():
    """VERSION_MAJOR/MINOR/PATCH must match the corresponding parts of VERSION string."""
    major, minor, patch = version.VERSION.split(".")
    assert version.VERSION_MAJOR == int(major), (
        f"VERSION_MAJOR {version.VERSION_MAJOR} does not match VERSION major {major}"
    )
    assert version.VERSION_MINOR == int(minor), (
        f"VERSION_MINOR {version.VERSION_MINOR} does not match VERSION minor {minor}"
    )
    assert version.VERSION_PATCH == int(patch), (
        f"VERSION_PATCH {version.VERSION_PATCH} does not match VERSION patch {patch}"
    )


def test_version_win_format():
    """VERSION_WIN must be 4 parts and end with '.0'."""
    parts = version.VERSION_WIN.split(".")
    assert len(parts) == 4, (
        f"VERSION_WIN must have 4 parts, got {len(parts)}: {version.VERSION_WIN!r}"
    )
    assert version.VERSION_WIN.endswith(".0"), (
        f"VERSION_WIN must end with '.0', got {version.VERSION_WIN!r}"
    )
    assert version.VERSION_WIN == f"{version.VERSION}.0", (
        f"VERSION_WIN {version.VERSION_WIN!r} must equal VERSION + '.0'"
    )


def test_version_tuple():
    """VERSION_TUPLE must be a tuple of 4 ints matching VERSION parts."""
    t = version.VERSION_TUPLE
    assert isinstance(t, tuple), f"VERSION_TUPLE must be a tuple, got {type(t)}"
    assert len(t) == 4, f"VERSION_TUPLE must have 4 elements, got {len(t)}"
    for i, elem in enumerate(t):
        assert isinstance(elem, int), f"VERSION_TUPLE[{i}] must be int, got {type(elem)}"
    major, minor, patch = version.VERSION.split(".")
    assert t == (int(major), int(minor), int(patch), 0), (
        f"VERSION_TUPLE {t} does not match expected ({major}, {minor}, {patch}, 0)"
    )
