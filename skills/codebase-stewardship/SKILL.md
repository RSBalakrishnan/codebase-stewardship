---
name: codebase-stewardship
description: Keeps a multi-developer product codebase correct and maintainable - a modular monolith with a util module - by enforcing low-level design (LLD), SOLID, module boundaries, coding standards, per-method unit tests, and regression tests, in a way a beginner can follow. Use this skill whenever anyone asks to add, change, fix, refactor, review, or test any code in the platform (multi-tenant RAG chatbot); to decide where code belongs (module vs util); to write unit or regression tests; to design a class/module/interface/API or an LLD; to onboard a new developer; or to check whether code is well designed - even if they never say SOLID, LLD, util, or regression. Also use for questions about the platform's features and business flows.
---

# Codebase Stewardship

## What this skill optimizes

The target is **the cost of making the next correct change, by a different developer, without breaking a third one's work.** SOLID, layering, module boundaries, and tests are means to that target, not goals in themselves. If a rule adds ceremony without lowering that cost, say so and record a deviation (see "Deviations").

Most defects in a team codebase sit on the **boundaries** between people's code: module interfaces, shared config, shared storage schemas, and the meaning of units and thresholds. So this skill makes boundaries explicit, and makes tools (tests, boundary checks) fail loudly when they are crossed.

**Audience.** Assume the person is capable but may be new to professional development. Give a one-sentence *why* for each rule you apply, show exact commands, define a term when first used, and never skip a safety step to save time. Rigor does not change: only the explanation does. If they are experienced, drop the explanations, keep the steps.

## Files in this skill

| Read this | When |
|---|---|
| `references/platform-map.md` | At the start of **every task**: features, business flows, how to build/verify the map |
| `references/modular-monolith.md` | Deciding where code goes; adding to `util`; creating or changing a module |
| `references/testing-guide.md` | Writing or changing any code (every change ships with tests); regression policy |
| `references/novice-playbook.md` | The person is new; step-by-step recipes; when to stop and ask a human |
| `references/solid-in-practice.md` | Designing or reviewing classes/interfaces/services |
| `references/lld-workflow.md` | Any non-trivial change: LLD note template and checklist |
| `references/product-invariants.md` | Touching ingestion, chunking, retrieval, cache, tenancy, flags, background jobs |
| `references/team-conventions.md` | PR/review rules, ADR template, definition of done, verification commands |
| `scripts/devkit.py` | `scaffold` test stubs, `audit` untested callables, `boundaries` import rules |
| `assets/templates/` and `assets/pyproject-testing-snippet.toml` | Test file patterns, fixtures, pytest markers |

## Terms (used precisely)

- **Module**: a folder that owns one business capability and exposes a **public API** (its `__init__.py`); others may use only that.
- **Util**: domain-agnostic, self-contained helpers organized by topic subpackage, depending on nothing else in the app.
- **Contract**: the preconditions, postconditions, invariants, and error behavior of an interface, not just its signature.
- **Responsibility**: one axis of change, i.e. one stakeholder or policy that would independently request modifications.
- **LLD note**: a 1-2 page design written before non-trivial code.
- **Platform map**: `docs/platform-map.md` in the repo: features, business flows, module and util registries, data ownership.

## Workflow

Follow in order. Do not skip Steps 0-1 even for small changes; most wrong-layer, duplicate, and boundary errors come from writing before understanding.

### Step 0 - Orient in the business
Read `docs/platform-map.md` (`references/platform-map.md`). Identify the feature(s) and flow(s) the task touches, the owning module, and the tests protecting them. If the map is missing, stale, or silent on this area, run the discovery procedure for that flow, record what you found, and mark anything unconfirmed as `UNKNOWN - ask <owner>`. Never fill a gap in business logic with a plausible guess. No agent or person understands every line of a large codebase; what this step guarantees is that **no change is made without locating its feature, flow, owner, tests, and callers.**

### Step 1 - Classify and locate
| Class | Examples | Gate |
|---|---|---|
| Trivial | local bug fix, rename, field inside one module, no new abstraction or contract change | Skip LLD note; apply checklists |
| Non-trivial | new module/interface, changed public API, multi-layer, storage/schema, tenancy, retrieval/ingestion behavior | LLD note **before** code |
| Review | a diff/file is pasted, or "is this good?" | Review mode below |

Unsure means non-trivial. Then: find where the responsibility already lives (search; do not guess from names), read neighbouring code and existing tests, and search for an existing implementation before writing one. Use the decision tree in `modular-monolith.md` section 5 to decide the destination.

### Step 2 - Design (non-trivial only)
Write the LLD note (`lld-workflow.md`): responsibilities, contracts, data/tenant impact, failure paths, alternatives, test plan. Ask at most one targeted question for a missing fact instead of assuming. For a beginner, also apply "STOP and ask" in `novice-playbook.md` section 4.

### Step 3 - Implement under the rules below, tests alongside
Write the test first for bug fixes. For everything else, write tests in the same change, never "later".

### Step 4 - Verify
Run, and report the actual result of:
```
pytest -m "unit or contract or regression"
python scripts/devkit.py audit app --tests-root tests/unit
python scripts/devkit.py boundaries --root .
ruff check . ; mypy <package>
```
Adapt commands to the repo's real toolchain (check `pyproject.toml`, CI config). State what was not run. Never claim "tests pass" without running them. Retrieval or ingestion behavior changes need an eval comparison before/after (`testing-guide.md` section 6); unit tests alone are insufficient evidence there.

### Step 5 - Update the map and report
Update `docs/platform-map.md` in the same change if a feature, flow step, module, public API, util function, flag, or data owner changed. Then report using the output format at the end.

## Core rules

### 1. Structure: modular monolith
- One deployable app; modules by business capability; other modules use a module **only through its public API**. No cycles. A module owns its data. Dependency direction: `interfaces -> modules -> core -> util`.
- **Domain code performs no I/O.** I/O lives in adapters behind abstractions the domain/service side owns. Only the composition root chooses concrete implementations.
- Boundaries are checked by `devkit.py boundaries` in CI, not by reviewer memory. Details: `modular-monolith.md`.

### 2. The util module (small generic features)
A function goes in `util/<topic>/` when **all three** are true: (1) domain-agnostic, (2) self-contained (no I/O, settings, or hidden state), (3) imports nothing from `modules/`, `core/`, or `interfaces/`. If it passes, put it in util immediately; do not wait for a second user. If it knows a business concept (tenant, chunk, FAQ, threshold...), it belongs in the owning module **however small it is.** Why: every module depends on util, so util has the highest blast radius; one business rule hidden there couples the whole product to it.
Util is organized by topic subpackage, never `utils.py`/`helpers.py`/`misc.py`. Every public util function has full unit tests, and changing a util signature is a contract change (update all callers in the same PR).

### 3. SOLID as operational tests
Full treatment with failure modes and limits: `solid-in-practice.md`.
- **SRP**: list who would independently ask for changes here; more than one answer means split.
- **OCP**: adding the next variant should be an addition, not an edit to an `if/elif` chain.
- **LSP**: every implementation passes the same contract test suite.
- **ISP**: consumers depend on the narrow Protocol they use, not the vendor client.
- **DIP**: policy owns the abstraction; concrete choice happens in the composition root; inject via constructor.

**Anti-over-engineering guard.** Create an abstraction (interface, factory, registry) only if: (a) two real implementations exist or are dated on the roadmap, or (b) it is an I/O boundary needing a test seam, or (c) the dependency is externally volatile. Otherwise write concrete code. Prefer composition over inheritance. Pure util helpers are plain functions, not classes.

### 4. Code standards
- **Units in names**: `chunk_size_tokens`, `timeout_seconds`. Ambiguous units (characters vs tokens) cause silent wrong behavior.
- **No magic numbers**: settings are typed, validated, documented (meaning and unit), read in one place, never via ad hoc environment lookups deep in code.
- **Types**: annotate public callables; validated models at trust boundaries; no raw dicts across modules.
- **Errors**: small domain exception hierarchy; translate vendor errors in adapters; no bare `except`; never swallow without logging context; do not use `None` to signal failure when `None` is a valid value.
- **Functions**: one level of abstraction; more than about four parameters suggests a missing parameter object; prefer pure functions in domain and util.
- **I/O discipline**: every network call has a timeout; retries only for idempotent operations, with backoff and a cap; no blocking calls in async paths.
- **Logging**: structured; carry `tenant_id` and request/job id; no secrets.
- **Comments** explain why, not what; delete commented-out code.

### 5. Testing (every change, every public method)
Details, case matrix, and regression policy: `testing-guide.md`.
- Every source file has a mirrored test file; **every public function and method has tests** covering: happy path, boundary, invalid input, failure path, plus idempotence/tenant scoping/ordering where they apply.
- Generate stubs with `python scripts/devkit.py scaffold <file>`. Stubs fail on purpose; fill each in or delete it with a stated reason.
- **Bug fix = failing regression test first** (`@pytest.mark.regression`, bug id in the name). Refactoring untested legacy code = characterization tests first. Pipeline stages = golden-output tests. Retrieval changes = eval comparison.
- Abstractions get **contract tests** run against every implementation, real and fake.
- **Prove a test can fail**: break the code on purpose and see it go red. A green test you never saw red is unverified.
- No live network or LLM calls in unit/regression tests. Never edit a test just to make it pass without stating why the expected behavior changed.

### 6. Working in a team
- **Contracts before code**: changing a public API, schema, or response shape needs all callers updated in the same PR, a compatibility note, and a contract test.
- **One concern per PR**; refactors and behavior changes are separate. Non-trivial changes get a second reviewer; owners of the touched module review it.
- **Decisions costly to reverse** (schema, embedding model, chunking policy, public API shape, new module, new core dependency) get an ADR (`team-conventions.md`).
- New dependency: state the reason, the alternative considered, and a maintenance/license check.
- Definition of Done includes tests, passing checks, and an updated platform map.

### 7. Product invariants
This product is multi-tenant and retrieval-based, which adds failure classes ordinary web rules do not cover (cross-tenant leakage, silent retrieval-quality regression, stale vectors after pipeline changes). Before touching ingestion, chunking, retrieval, cache, tenancy, flags, or background jobs, read `product-invariants.md`.

## Deviations
Rules are defaults. To deviate, write one line in the PR or LLD: **rule, reason, blast radius, when to revisit.** A deviation without a reason is a defect. Legitimate cases: emergency hotfix (follow-up ticket with a date), throwaway spike (label `SPIKE - not for merge`), measured performance need (attach the measurement).

## Review mode
Do not summarize what the code does and do not open with praise. Check in this order and stop expanding once the highest-severity class present is covered:
1. Correctness and invariants (tenant isolation, wrong units, data loss, unhandled failure)
2. Contracts and boundaries (module rules, util admission, public API changes, callers updated)
3. Design (SOLID tests, unjustified or missing abstraction, duplicated implementation)
4. Tests (does a test fail if the behavior breaks? public methods covered? failure paths? regression test for bug fixes?)
5. Maintainability (naming, structure, comments, map updated)

Label anything you did not run or trace as "unverified".

## Output format
For reviews and non-trivial work:
```
## Verdict
<merge / merge after fixes / redesign> - one sentence with the deciding reason

## Findings (highest severity first)
[Blocker|Major|Minor|Nit] <file:line or component>
- Rule violated: <which rule>
- Failure mode: <what breaks, for whom, under what condition>
- Fix: <specific change>
- Verify: <test or check proving it fixed>

## Verification performed
<commands run and results; what was NOT run>

## Assumptions and unverified items
## Open questions   (at most three, each targeted and answerable)
```
For trivial changes: the change, the tests added, the checks run and their results, and any assumption.
