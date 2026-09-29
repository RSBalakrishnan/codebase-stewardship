# Team Conventions

Shared rules so that developers can work in parallel without negotiating basics each time. Where the team already has a convention, follow it; this file defines the defaults and the reasoning.

## Contents
1. Repository structure
2. Change workflow and PR rules
3. Review checklist
4. Testing strategy
5. Verification commands
6. ADR template
7. Definition of Done
8. Tech-debt handling

---

## 1. Repository structure

Modular monolith: modules by business capability, a small `core`, a topic-organized `util`, thin `interfaces`. Full rules, the util admission test, and the "where does this go" decision tree are in `modular-monolith.md`. Adjust names to match the existing repo; do not restructure without an ADR.

```
app/
  modules/<module>/   # __init__.py = public API; service.py, domain/, adapters/, schemas.py
  core/               # platform kernel: settings, TenantContext, base exceptions, logging
  util/<topic>/       # domain-agnostic helpers; imports nothing from modules/core/interfaces
  interfaces/         # HTTP routes, widget endpoints, workers, CLI (thin)
  composition.py      # the only place concrete implementations are wired
docs/
  platform-map.md     # features, business flows, module/util registries, data ownership
  adr/                # architecture decision records
tests/
  unit/               # mirrors app/: tests/unit/<same path>/test_<file>.py
  contract/           # one suite per abstraction, run against every implementation
  integration/        # real containers (vector store, DB); no live LLM/network
  regression/         # golden files and characterization fixtures
  eval/               # retrieval/answer quality sets and stored baselines
  fakes/              # in-memory fakes that pass the contract suites
```

Other modules import a module only via its package root (`from app.modules.x import y`). Importing its private files is a boundary violation and fails the boundary check.

## 2. Change workflow and PR rules

- Branch from the main line; keep the branch short-lived. Long-lived branches are where integration defects accumulate.
- **One concern per PR.** A refactor and a behavior change are separate PRs (or at minimum separate commits) so each can be reviewed and reverted alone.
- **Size**: if a reviewer cannot understand the PR in one sitting (roughly 400 changed lines excluding generated code is a useful alarm), split it or add a design note. This is a heuristic, not a law; large mechanical renames are fine.
- **Contract changes**: update every caller in the same PR, add or update the contract test, note compatibility in the description.
- **Commits**: `type(scope): imperative summary` (`fix(chunker): count tokens, not characters`). The body states why, not what.
- **PR description** must contain: problem, approach, alternatives rejected (if non-trivial), risks/blast radius, how it was verified, rollback.
- Nobody merges their own non-trivial change without a second reviewer. Owners of the touched module (via CODEOWNERS) review changes to it.
- CI must pass before merge; do not merge with a failing or skipped check "temporarily".

## 3. Review checklist

Reviewers check in this order (highest cost of a miss first):

1. **Correctness**: tenant scoping, units, off-by-one, failure handling, resource bounds.
2. **Contracts**: interface/schema/API changes, callers updated, backward compatibility.
3. **Design**: layering, SOLID tests, unjustified or missing abstraction, duplication of an existing implementation.
4. **Tests**: does each new behavior have a test that fails without it? Is there a regression test for each bug fix? Are failure paths covered?
5. **Operability**: logs carry tenant/request ids, timeouts and retries set, config documented, migration/rollback defined.
6. **Readability**: naming, comments explain why, dead code removed.

Review comments state the failure mode, not a preference. Label nits as nits. An approval means "I traced the risky paths", not "I skimmed it".

## 4. Testing strategy

| Level | Scope | Uses | Purpose |
|---|---|---|---|
| Unit | domain functions, use cases | fakes for abstractions | fast logic verification |
| Contract | each abstraction | parameterized over real + fake implementations | ensures LSP; keeps fakes honest |
| Integration | adapters with real dependencies | containers | catches vendor-behavior mismatches |
| Evaluation | retrieval and answer quality | fixed labeled question sets | catches quality regressions that pass all unit tests |

Rules:
- Tests do not call live LLMs or external sites in CI (slow, costly, nondeterministic). Record fixtures or use fakes at the abstraction boundary.
- A bug fix starts with a failing test that reproduces the bug.
- Test behavior through public interfaces; tests that assert private call sequences break on every refactor and protect nothing.
- Coverage percentage is a weak proxy. Prefer: every invariant and every failure path in the LLD has a test.
- Flaky tests are defects with an owner and a deadline, not something to rerun.

## 5. Verification commands

Adapt to the repo's actual toolchain (check `pyproject.toml`, `Makefile`, CI config first; do not assume). Python defaults:

| Purpose | Typical command |
|---|---|
| Lint/format | `ruff check .` and `ruff format --check .` |
| Types | `mypy <package>` (strict on new modules) |
| Unit + contract + regression | `pytest -m "unit or contract or regression"` |
| Integration | `pytest tests/integration` (containers running) |
| Module/util boundaries | `python scripts/devkit.py boundaries --root .` (private imports, util/core rules, module cycles) |
| Untested public callables | `python scripts/devkit.py audit app --tests-root tests/unit` |
| Domain purity (optional, stricter) | import-linter contracts if the team adopts it: domain must not import adapters |
| Dead code / unused deps | `vulture`, dependency audit as the team prefers |

If a command was not run, the report says so. "Should pass" is not verification.

## 6. ADR template

Use for decisions that are expensive to reverse: schema/payload shape, embedding model, chunking policy, public API shape, new core dependency, layer/structure changes.

```
# ADR-<n>: <decision title>
Status: proposed | accepted | superseded by ADR-<m>
Date / Deciders:

## Context
The forces and constraints, including the ones that make this hard.

## Decision
What we will do, stated plainly.

## Alternatives considered
Each with why it lost.

## Consequences
Good, bad, and what becomes harder. Include migration/re-ingestion cost and
how to detect that this decision was wrong.
```

## 7. Definition of Done

- [ ] Behavior matches the LLD/acceptance criteria and the invariants still hold
- [ ] New/changed behavior has tests that fail without the change
- [ ] Every new/changed public callable has unit tests (`devkit.py audit` clean); bug fixes have a regression test that failed first
- [ ] Lint, types, tests, and boundary check pass in CI
- [ ] `docs/platform-map.md` updated if a feature, flow, module, public API, util function, flag, or data owner changed
- [ ] No new hardcoded tenant- or client-specific logic; config values named with units
- [ ] Logs/metrics carry tenant and request/job ids for new paths
- [ ] Docs/ADR/LLD updated where a contract or decision changed
- [ ] Migration and rollback steps exist where data or schema changed
- [ ] Reviewer traced the high-risk paths

## 8. Tech-debt handling

- Record debt in a visible register with: what, why it was accepted, cost of carrying it, and a trigger for repayment. Unrecorded debt is invisible to the rest of the team.
- A `TODO` in code must reference a ticket or owner; bare TODOs are removed in review.
- Opportunistic cleanup is limited to the code you are already changing, and is a separate commit from the behavior change.
