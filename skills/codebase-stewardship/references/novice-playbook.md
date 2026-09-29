# Playbook for Developers New to the Codebase

Written so someone who is new to professional development can make safe, correct changes in a product codebase. The agent following this skill should treat the person as capable but inexperienced: explain **why** in one sentence, show exact commands, define a term the first time it appears, and never skip a safety step to save time.

The safety net is not memorizing everything. It is a fixed routine, tests that fail loudly, and boundary checks that a tool runs for you.

## Contents
1. The routine (every task)
2. Vocabulary
3. Recipe cards
4. STOP and ask a human when...
5. Common mistakes and how to recognize them
6. Worked example: "add a function that removes extra spaces"

---

## 1. The routine (every task)

1. **Understand the task in one sentence**: "When X happens, the system should Y." If you cannot write it, ask.
2. **Open `docs/platform-map.md`.** Find the feature and flow you are touching, its owning module, and its tests. Missing? See `platform-map.md` section 2.
3. **Find where the code lives** with the decision tree in `modular-monolith.md` section 5. Do not create a new place if one exists.
4. **Read before writing**: the owning module's public API, neighbouring code, and the existing tests. Copy the existing style.
5. **Write the test first when you can** (always for bug fixes).
6. **Make the smallest change** that makes the test pass. Small changes are easier to review and to undo.
7. **Run the checks**: your tests, then the boundary check, then the audit, then lint and types.
8. **Update docs** (platform map, docstrings) if you changed behavior or added a feature.
9. **Write the PR description**: what, why, how you verified, what could break.
10. **Ask for review.** Reviews are how the team catches what one person cannot see.

## 2. Vocabulary

| Term | Plain meaning |
|---|---|
| Module | A folder that owns one business capability and hides its insides |
| Public API | The names a module exports in its `__init__.py`; the only things others may use |
| Util | Small, generic helpers with no business knowledge, usable by all modules |
| Tenant | One client company using the platform; their data must never mix with another's |
| Unit test | A fast check of one function, using fakes instead of real services |
| Regression test | A check that stops a fixed or working behavior from breaking again |
| Contract | The promises an interface makes: inputs it accepts, outputs it returns, errors it raises |
| Fake | A simple stand-in for a real service (a fake store held in memory) used in tests |
| Flag | A setting that turns a behavior on or off, often per tenant |
| Fixture | Reusable test setup |

## 3. Recipe cards

### A. Fix a bug
1. Reproduce it. Write a test that fails with the bug's symptom; mark `@pytest.mark.regression`; put the bug id in the name.
2. Confirm the test fails **for the right reason**.
3. Find the owning module through the platform map. Fix there, not in a caller.
4. Confirm the test passes and the rest of the suite still passes.
5. PR: link the bug, state root cause (not just symptom), name the regression test.

### B. Add a small generic helper
1. Apply the util admission test (`modular-monolith.md` section 4). All three YES -> `app/util/<topic>/`. Otherwise it belongs in a module.
2. `python scripts/devkit.py scaffold app/util/<topic>/<file>.py`; fill in every stub.
3. Docstring: input, output, edge cases. Type hints on everything.
4. Grep for existing helpers that already do this. Duplicates are defects.

### C. Add a feature inside an existing module
1. Write down the user-visible behavior and the acceptance cases.
2. Non-trivial (new interface, touches storage, touches more than one layer)? Write a short LLD note first (`lld-workflow.md`), get it reviewed.
3. Add pure logic to the module's `domain/`, I/O to `adapters/`, sequencing to `service.py`.
4. Export a new public name in `__init__.py` only if another module needs it.
5. Tests for every new public callable; contract test if you added an interface.
6. Put risky new behavior behind a per-tenant flag that defaults **off**.
7. Add the feature row and flow changes to the platform map.

### D. Change a setting or threshold
1. Find where it is defined in config. Never edit a literal inside code.
2. Check its **unit and meaning** in the map glossary (tokens vs characters, which stage's score).
3. If it changes what is stored or retrieved, this is a retrieval change: eval comparison before and after is required.
4. Change the default only through a reviewed PR that states the evidence.

### E. Refactor
1. No tests? Write characterization tests first (`testing-guide.md` section 6).
2. Change structure only, no behavior, in its own PR.
3. Tests must stay green without being edited. If you must edit a test, you changed behavior: stop and split the work.

### F. Change something another module owns
1. Do not edit its internals. Open the module's public API.
2. Need something not exported? Ask its owner to export it deliberately (a small PR to that module).
3. Never read its database/collection directly.

### G. Add a new module
Requires a short LLD note and an ADR-lite (one paragraph: responsibility, public API, dependencies, owner). A new module is a boundary decision; get a reviewer before creating the folder.

## 4. STOP and ask a human when...

Do not proceed on your own guess if the change:
- touches **tenant scoping**, authentication, or anything that decides whose data is visible
- changes a **stored schema/payload**, chunking, embedding, or anything requiring **re-ingestion**
- changes a **public API** or response shape that others (including the widget) rely on
- involves **secrets, credentials, billing, or personal data**
- needs a **new dependency** or a new module
- makes an existing test fail and the only quick fix seems to be editing the test
- contradicts the platform map, or the map has `UNKNOWN` for the area
- you cannot explain, in plain words, why the change is safe

Asking early is cheap. A wrong change to these areas can affect every client.

## 5. Common mistakes and how to recognize them

| Mistake | Symptom | Fix |
|---|---|---|
| Fixing the symptom in the caller | Same bug appears from another entry point | Fix at the owning module |
| Editing the test to make it pass | Test changed in the same diff as the code, no reason given | Restore; decide whether behavior or test is wrong, explain |
| Putting business code in util | Function name contains a domain word (faq, tenant, chunk) | Move to owning module |
| Importing a private path of another module | Boundary check fails | Use the public API or ask for an export |
| Hardcoding a value | Number or string literal inside logic | Named setting with unit and default |
| Copy-paste of existing code | Two near-identical functions | Extract; search first next time |
| Swallowing errors | `except: pass` | Catch specific errors, log with context, or let it propagate |
| Testing the implementation | Test breaks when you rename a private function | Test inputs and outputs of the public callable |
| Green stub tests | `pytest.fail("TODO")` removed without writing a real assertion | Every test must assert an expected result |

## 6. Worked example: "add a function that removes extra spaces"

1. **Task sentence**: "Given text, return it with runs of whitespace collapsed to single spaces and ends trimmed."
2. **Where?** Business concepts involved? No. Admission test: domain-agnostic yes, self-contained yes, imports no modules yes -> `app/util/text/normalize.py`.
3. **Search first**: `grep -rn "whitespace" app/` to be sure it does not already exist.
4. **Write it**:
   ```python
   def collapse_whitespace(text: str) -> str:
       """Collapse runs of whitespace to one space and strip the ends.

       Empty or whitespace-only input returns "". Raises TypeError if text is not str.
       """
       if not isinstance(text, str):
           raise TypeError("text must be str")
       return " ".join(text.split())
   ```
5. **Scaffold tests**: `python scripts/devkit.py scaffold app/util/text/normalize.py`, then fill: happy path (`"a   b\t\nc"` -> `"a b c"`), boundaries (empty, only spaces, single char, non-breaking space), invalid input (`None` raises `TypeError`), and idempotence.
6. **Prove a test can fail**: change `" ".join(text.split())` to `text.strip()`; the happy-path test must fail. Restore.
7. **Run checks**: `pytest tests/unit/util/text`, `devkit.py audit app/util`, `devkit.py boundaries --root .`, lint, types.
8. **Update** the util registry in the platform map. Open the PR.
