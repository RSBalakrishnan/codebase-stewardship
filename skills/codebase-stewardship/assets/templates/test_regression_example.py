"""TEMPLATE regression tests. Three kinds; pick by situation.

1) BUG REGRESSION  - write this FIRST when fixing a bug; watch it fail; then fix.
2) CHARACTERIZATION - pin what legacy code does TODAY before you refactor it.
3) GOLDEN OUTPUT    - compare a pipeline stage's output to an approved file.
"""
import json
from pathlib import Path

import pytest

GOLDEN = Path(__file__).parent / "golden"


# 1) Bug regression --------------------------------------------------------------
@pytest.mark.regression
def test_chunker__counts_tokens_not_characters__bug_CHUNK_001():
    """BUG CHUNK-001: chunk size was measured in characters, producing chunks far
    smaller than configured. Reproduce with input whose char count and token count differ.
    """
    # text = "word " * 1000
    # chunks = chunk_text(text, chunk_size_tokens=200)
    # assert all(count_tokens(c.text) <= 200 for c in chunks)
    # assert len(chunks) < 1000 / 100   # would fail under the char-count bug
    pytest.fail("TODO: reproduce the real bug here")


# 2) Characterization ------------------------------------------------------------
@pytest.mark.regression
@pytest.mark.parametrize("case", ["faq_page", "plain_article"])
def test_legacy_parser__current_behaviour_is_pinned(case):
    """Not a statement that the behaviour is RIGHT, only that it must not change
    by accident during refactoring. Change it deliberately, in a separate PR."""
    # html = (GOLDEN / f"{case}.html").read_text()
    # assert parse(html) == json.loads((GOLDEN / f"{case}.expected.json").read_text())
    pytest.fail("TODO: pin current output")


# 3) Golden output ---------------------------------------------------------------
@pytest.mark.regression
def test_prompt_assembly__matches_approved_output():
    """If this fails after an INTENTIONAL change: review the diff, get a reviewer's
    approval, then update the golden file in the same PR with the reason in the message."""
    # actual = assemble_prompt(fixture_query, fixture_chunks)
    # assert actual == (GOLDEN / "prompt_basic.txt").read_text()
    pytest.fail("TODO: add golden file")
