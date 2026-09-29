# Modular Monolith and the Util Module

Read this before deciding where any new code lives, and before creating a module or adding to `util`.

## Contents
1. What a modular monolith is (and why it fits a team)
2. Layout
3. Module rules
4. The util module: admission test and rules
5. Where does this code go? (decision tree)
6. Communication and data ownership
7. Enforcement
8. Anti-patterns
9. Candidate modules for this product

---

## 1. What a modular monolith is

One deployable application, internally divided into **modules**, where each module owns one business capability and other modules can use it only through its **public API**. It gives most of the isolation benefit of microservices (independent reasoning, parallel work, clear ownership) without network calls, distributed failure, or a heavy deployment pipeline. That trade suits a small team and a small server.

It only works if the boundaries are **real**. If any module can import any file of any other module, it is an ordinary monolith with folders. Boundaries must be checked by a tool (section 7), not by good intentions.

## 2. Layout

```
app/
  modules/
    <module>/                 # one business capability
      __init__.py             # PUBLIC API: the only names other modules may import
      service.py              # use cases / orchestration for this module
      domain/                 # pure logic and types (no I/O, no framework imports)
      adapters/               # this module's I/O: DB, vector store, HTTP clients
      schemas.py              # typed data crossing the module boundary
      config.py               # this module's settings
  core/                       # platform kernel: settings loading, TenantContext, base exceptions, logging setup
  util/                       # domain-agnostic helpers (section 4)
    text/  time/  ids/  retry/  validation/  ...
  interfaces/                 # HTTP routes, workers, CLI: thin, they only call module public APIs
  composition.py              # the ONLY place concrete implementations are chosen and wired
tests/
  unit/ (mirrors app/)   contract/   integration/   regression/   eval/   fakes/
```

Small modules do not need every folder. Create `domain/` or `adapters/` when there is something to put in them, not before.

Dependency direction: `interfaces -> modules -> core -> util`. Arrows never point the other way. Modules may depend on each other only through public APIs and without cycles.

## 3. Module rules

1. **One module = one business capability**, describable in one sentence without "and". If you cannot, split it.
2. **Public API is `__init__.py`.** Other modules import `from app.modules.retrieval import search`, never `from app.modules.retrieval.store import X`. If you need something that is not exported, ask the module's owner to export it deliberately.
3. **Public API is a contract.** Changing an exported name, signature, or return shape means updating every caller in the same change, plus a contract test. Prefer adding over changing.
4. **Pass typed data across boundaries** (dataclasses/pydantic models defined in the module's `schemas.py`), not raw dicts and not the other module's internal objects.
5. **A module owns its data.** Only the owning module reads or writes its tables/collections/files directly. Others go through the public API. If two modules must share a stored schema (for example ingestion writes what retrieval reads), one module owns the schema and exposes it as a typed contract; the other depends on the contract, not on raw storage details.
6. **No cycles.** If A imports B and B imports A, extract the shared concept into a third module or into `core`, or invert one dependency with an interface owned by the caller. The check script reports cycles.
7. **No module imports `interfaces`.** Routes call modules; modules never call routes.
8. **Tenant scoping is enforced inside the module that touches tenant data** (see `product-invariants.md`), not left to callers.
9. **Each module has a matching test folder** mirroring its structure, and a section in `docs/platform-map.md` (owner, responsibility, public API, dependencies).

## 4. The util module

**Why util needs strict rules.** Every module depends on util. That gives util the highest "fan-in" in the codebase: a wrong change in util can break every module at once. So util must be the *most stable* and *least knowledgeable* code in the repo. A util function that knows a business rule couples the whole product to that rule.

### Admission test: all three must be YES

1. **Domain-agnostic**: could this function be copied unchanged into an unrelated product? (`collapse_whitespace`: yes. `clean_faq_answer`: no, it knows what an FAQ is.)
2. **Self-contained**: does it depend only on its arguments, the standard library, third-party libraries, and other util code? No hidden globals, no settings lookups, no database/network calls, no reading tenant data.
3. **Leaf dependency**: does it import nothing from `modules/`, `core/`, or `interfaces/`? (The check script fails the build otherwise.)

If all three are YES, the function goes in util **now**, even if only one module uses it today. Small, generic helpers belong there.
If question 1 is NO, the function belongs in the module that owns the concept, however small it is. Business-aware code does not go in util.
If question 2 is NO because it does I/O (HTTP retry wrapper, file reading), it is an adapter: put it in the owning module's `adapters/` or in `core/` if truly platform-wide.

### Util rules

- Organize by **topic subpackage**: `util/text/`, `util/time/`, `util/ids/`, `util/retry/`, `util/validation/`. Never `util/misc.py`, `helpers.py`, `common.py`, or one giant `utils.py`.
- Each function: type hints, a docstring stating input, output, and what it does on edge cases (empty, `None`, unicode), and **no side effects** unless the name says so.
- **100% of public util functions have unit tests** (`devkit.py audit app/util` must report none missing). Util is where a test-per-method rule pays back most, because a bug is inherited by everyone.
- **Stability policy.** Util signatures are public contracts. To change one: grep all callers, update them in the same PR, or add a new function and deprecate the old with a removal date. Never silently change what an existing util function returns.
- Keep util small and boring. A subpackage that grows beyond about ten functions or mixes topics should be split. A util function used by no one for a long time should be deleted.
- No new third-party dependency for a util function that is a few lines of standard-library code.
- Naming: verbs for actions (`collapse_whitespace`), nouns/`is_`/`has_` for predicates and values. Names say what, not how.

## 5. Where does this code go? (decision tree)

```
Is it HTTP/route/worker/CLI glue (parse request, call something, format response)?
   yes -> interfaces/
Does it use business concepts (tenant, page, chunk, FAQ, answer, score threshold...)?
   yes -> the module that owns that concept (never util)
      Is it pure logic with no I/O?             -> that module's domain/
      Does it talk to DB / vector store / HTTP? -> that module's adapters/
      Does it sequence steps of a use case?     -> that module's service.py
No -> does it pass the util admission test (section 4)?
   yes -> util/<topic>/
   no  -> is it platform-wide plumbing (settings, TenantContext, base exceptions, logging)? -> core/
          otherwise STOP and ask: the responsibility is unclear, which is a design question.
```

## 6. Communication and data ownership

- **Default: call the other module's public API directly** (in-process function or class). It is simple, debuggable, and typed.
- **Use a callback/event interface only when** module A must trigger reactions in B without knowing B exists (for example "ingestion finished" notifying cache invalidation). The interface is owned by the module that emits it. Do not introduce an event bus for two callers.
- A module must never import another module's `adapters/`, `domain/`, or `service.py` directly, and must never query another module's storage.

## 7. Enforcement

Run in CI on every PR (fails the build):

```
python scripts/devkit.py boundaries --root .        # private imports, util/core rules, module cycles
python scripts/devkit.py audit app --tests-root tests/unit   # public callables without tests
```

`boundaries` checks: modules import other modules only through the package root; `util` and `core` never import `modules`; `util` never imports `core`; no cycles between modules. It is intentionally simple and dependency-free. It does not check runtime coupling (shared database tables, shared files, global state). Those need review and the data-ownership rule.

## 8. Anti-patterns

| Anti-pattern | Why it hurts | Instead |
|---|---|---|
| Business rule in util "because it is small" | Hidden coupling; every module depends on that rule | Put it in the owning module |
| `from app.modules.x.service import y` from another module | Bypasses the contract; x cannot refactor safely | Export `y` from x's `__init__.py` deliberately |
| Two modules reading the same table directly | Schema change breaks both silently | One owner, typed contract |
| Circular module dependency | Neither module can be understood or tested alone | Extract shared concept / invert dependency |
| `core` growing into a second util | Grab-bag with business knowledge | `core` holds only platform kernel; everything else has an owner |
| A module per class/file | Ceremony without isolation benefit | A module is a business capability |
| Cross-module logic in `interfaces/` | Business rules hidden in routes | Move into a module use case |

## 9. Candidate modules for this product

Derived from the architecture described so far. **Treat as candidates to verify against the repo and the team, not as facts.**

| Candidate module | One-sentence responsibility |
|---|---|
| `tenants` | Tenant identity, per-tenant settings, and feature-flag resolution |
| `ingestion` | Acquire client content (scrape/upload), clean and normalize it, and hand it to indexing |
| `chunking` | Split documents into retrieval units (structured units such as FAQs extracted whole first) |
| `indexing` | Embed chunks and write them to the vector store with pipeline versioning |
| `retrieval` | Hybrid search, fusion, thresholds, and reranking for a tenant's query |
| `answering` | Prompt assembly, LLM call, fallback policy, and post-processing |
| `cache` | Semantic/exact response cache with tenant- and version-aware keys |
| `evaluation` | Eval-set generation and retrieval/answer quality measurement (background jobs with status) |
| `widget` (interface) | The embeddable script and the public chat endpoints |

If the real repo differs, the repo wins; record the difference in `docs/platform-map.md` and adjust.
