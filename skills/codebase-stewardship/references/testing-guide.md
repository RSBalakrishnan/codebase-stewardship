# Testing Guide: Unit Tests per Method, and Regression

Read this whenever you write, change, or delete code. Every code change ships with tests. This file explains what to test, how to write each test, how regression protection works, and how to prove your tests are real.

## Contents
1. Definitions
2. The rule: one test file per source file, tests for every public method
3. The case matrix (what to test for each method)
4. How to write one unit test
5. Fakes, not mocks of internals
6. Regression testing
7. Which tests run when
8. Feature-to-test traceability
9. Proving a test can fail
10. Workflow with devkit.py
11. What NOT to do

---

## 1. Definitions

- **Unit test**: checks one function or method in isolation, fast, no network or database, dependencies replaced by fakes.
- **Contract test**: one suite of assertions run against *every* implementation of an abstraction (real adapter and fakes), so they cannot drift apart.
- **Integration test**: the code with a real dependency (vector store, database) in a container. Catches vendor-behavior mismatches unit tests cannot.
- **Regression test**: a test that exists to stop something that once broke, or that currently works, from breaking again. Three kinds:
  - *Bug regression*: reproduces a specific past bug.
  - *Characterization*: records what legacy code does today, before you refactor it. It says "this must not change by accident", not "this is correct".
  - *Golden output*: compares a stage's output to an approved stored file.
- **Evaluation (eval) test**: measures retrieval or answer quality on a labeled question set and compares to a stored baseline. Needed because a retrieval change can pass every unit test and still make answers worse.

## 2. The rule

- Every source file `app/<path>/<name>.py` has `tests/unit/<path>/test_<name>.py`.
- Every **public** function and method (name not starting with `_`) has tests. Private helpers are tested *through* the public callables that use them; testing private methods directly welds tests to the implementation and breaks on every refactor.
- Constructors with parameters are tested too (`__init__`): invalid arguments must be rejected as documented.
- Abstractions (Protocol/ABC) get **contract tests**, not unit tests.
- `devkit.py audit` lists public callables with no filled-in test. CI runs it; it must report zero missing for `util` and for every module's public API.

## 3. The case matrix

For each public callable decide, explicitly, which of these apply. "Not applicable" is a valid answer only when you can say why in one sentence.

| Case | Ask | Typical examples |
|---|---|---|
| Happy path | What is the normal, valid use? | Typical input gives typical output |
| Boundary | What are the edges? | Empty string/list, one item, exactly at the limit, limit plus one, `0`, negative, very long, unicode, whitespace-only |
| Invalid input | What must be rejected? | Wrong type, `None`, out-of-range value; assert the specific documented exception |
| Failure path | What if a dependency fails? | Store raises, timeout, LLM returns garbage; assert the documented behavior (raises, falls back, retries) |
| Idempotence / determinism | Does it claim to be repeatable? | Same input twice gives the same result; running an ingest twice does not duplicate |
| Tenant scoping | Does it touch tenant data? | Data for tenant B never appears for tenant A (always use two tenants in the fixture) |
| Ordering / time | Does order or time matter? | Sorted output, stable ordering of ties, frozen clock for expiry |

`devkit.py scaffold` generates the first four cases per callable as **failing** stubs. Add the others when they apply.

## 4. How to write one unit test

Structure: **Arrange** (build inputs), **Act** (call the one thing under test), **Assert** (check the result).

```python
def test_collapse_whitespace__happy_path():
    # Arrange
    raw = "a   b\t\nc"
    # Act
    result = collapse_whitespace(raw)
    # Assert
    assert result == "a b c"
```

Rules:
- **Name**: `test_<function>__<case>` or `test_<class_snake>__<method>__<case>`. The name states the situation; a failing test's name should tell you what broke without reading the body.
- **One behavior per test.** If the name needs "and", split it.
- **Assert on the result or observable effect**, not on how it was computed (not "this internal helper was called twice").
- Use `pytest.mark.parametrize` for many inputs of one behavior (boundary tables).
- Assert the **specific exception** with `pytest.raises(SpecificError, match="...")`, not bare `Exception`.
- Tests are independent: no order dependence, no shared mutable state, no real clock, no randomness without a fixed seed, no network.
- A test is documentation. Use realistic-looking data, not `foo`/`bar`, when the domain matters.

## 5. Fakes, not mocks of internals

Replace **abstraction boundaries** (vector store, LLM client, clock, scraper) with small in-memory fakes that obey the same contract. Do not patch private functions or assert call sequences; such tests fail on harmless refactors and pass on real bugs.

A fake is only trustworthy if it passes the **same contract suite** as the real adapter (see `assets/templates/test_contract_example.py`).

## 6. Regression testing

**Policy**
1. **Bug fix = test first.** Write a test that reproduces the bug and *fails*. Then fix. Mark it `@pytest.mark.regression` and put the bug id in the name and docstring (`..._bug_CHUNK_001`). A bug fix without a regression test is incomplete, because the same bug can silently return.
2. **Refactor legacy code = characterization tests first.** Before restructuring code that lacks tests, pin its current behavior on representative inputs. Then refactor; those tests must stay green. Behavior changes go in a *separate* PR that updates them deliberately.
3. **Pipeline stages get golden-output tests** (chunker output, prompt assembly, parsed structures) on small stored fixtures. When one fails after an *intentional* change, a reviewer approves the diff, then the golden file is updated in the same PR with the reason. An auto-updated golden file that no one reviewed protects nothing.
4. **Retrieval-affecting changes get an eval regression check**: run the eval set before and after and compare hit rate and per-category failures against the stored baseline. A drop in any category beyond the agreed tolerance blocks the change or requires a written decision.
5. **The regression suite only grows.** Deleting a regression test requires stating why the protected behavior no longer matters.
6. **Flaky tests are defects.** Owner and deadline, not "rerun until green". A flaky regression suite gets ignored, which is worse than none.

**What "regression suite" means concretely**: all tests marked `regression` plus all unit and contract tests. It runs on every PR.

## 7. Which tests run when

| Trigger | Runs | Target time |
|---|---|---|
| Local, while coding | The test file(s) for what you changed | seconds |
| Every PR (CI) | unit + contract + regression, boundary check, audit, lint, types | minutes |
| PR touching adapters, schemas, storage | plus integration (containers) | minutes |
| PR touching chunking, embedding, fusion, thresholds, reranking, prompts | plus eval comparison to baseline | as needed |
| Nightly on the main line | everything, including slow and integration | any |
| Before release | full suite plus eval, results recorded | any |

Commands (adjust to the repo):
```
pytest -m "unit or contract or regression"          # PR default
pytest -m integration                               # needs containers
pytest -m eval                                      # quality comparison
pytest tests/unit/util/text/test_normalize.py -x    # just what you touched
```

## 8. Feature-to-test traceability

In `docs/platform-map.md`, the feature catalog has a **Tests** column listing the test files/markers that protect each feature. Consequences:
- A feature with an empty Tests cell is unprotected: say so in the PR.
- Changing a feature means running its listed tests and adding to them.
- A test that maps to no feature is either testing a private detail or the map is incomplete; check.

## 9. Proving a test can fail

A green test proves nothing until you have seen it red for the right reason.
1. **Break it on purpose (manual mutation)**: temporarily change the code (flip a comparison, remove a branch, return early). The test for that behavior must fail. If it stays green, the test does not test that behavior; fix the test.
2. **For a bug fix**: run the new test *before* the fix and confirm it fails with the bug's symptom.
3. Optional, stronger: run a mutation-testing tool (for example `mutmut`) on util and other high-fan-in code and review surviving mutants.

Coverage percentage tells you which lines ran, not whether anything was checked. Use it to find *untested* code, never as a target to hit.

## 10. Workflow with devkit.py

```
python scripts/devkit.py scaffold app/util/text/normalize.py   # writes failing stubs
# fill in each stub (or delete it and state why in the PR)
pytest tests/unit/util/text/test_normalize.py
# prove it can fail (section 9)
python scripts/devkit.py audit app --tests-root tests/unit     # nothing missing?
python scripts/devkit.py boundaries --root .                   # boundaries intact?
```

`scaffold` is safe to re-run: it adds stubs only for public callables that have no test yet and never overwrites existing tests. Stubs fail on purpose; a green placeholder would be a false signal. Requires `pytest-asyncio` for `async` callables.

## 11. What NOT to do

- Do not write tests that only re-implement the code (`assert f(x) == x + 1` where the code is `x + 1` and the expectation was copied from it). Derive expected values independently: from the spec, a hand calculation, or a known-good example.
- Do not comment out or `skip` a failing test to get green. Fix the code, fix the test, or delete it with a stated reason.
- Do not call live LLMs, live websites, or shared databases from unit/regression tests.
- Do not share state between tests through module-level variables or the database.
- Do not change a test and the code it protects in the same edit without explaining why the expectation changed.
- Do not treat the eval score or coverage as the goal; they are instruments.
