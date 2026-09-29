"""TEMPLATE unit test for a small util function.

Function under test (in app/util/text/normalize.py):
    def collapse_whitespace(text: str) -> str: ...
Read this as a pattern, then run: python scripts/devkit.py scaffold <your_file>.
"""
import pytest

from app.util.text.normalize import collapse_whitespace


def test_collapse_whitespace__happy_path():
    assert collapse_whitespace("a   b\t\nc") == "a b c"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", ""),                 # empty
        ("   ", ""),              # only whitespace
        ("x", "x"),               # single char
        ("\u00a0a\u00a0b", "a b"),  # non-breaking spaces (unicode)
    ],
)
def test_collapse_whitespace__boundary(raw, expected):
    assert collapse_whitespace(raw) == expected


def test_collapse_whitespace__invalid_input():
    with pytest.raises(TypeError):
        collapse_whitespace(None)  # type: ignore[arg-type]


def test_collapse_whitespace__is_idempotent():
    once = collapse_whitespace("a   b")
    assert collapse_whitespace(once) == once
