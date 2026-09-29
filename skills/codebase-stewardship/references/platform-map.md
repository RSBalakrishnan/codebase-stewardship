# Platform Map: Features and Business Flows

The agent cannot safely change code it does not understand, and it cannot understand the platform by reading files at random. The fix is a **living document in the repo**: `docs/platform-map.md`. It records every feature, every business flow, and who owns what. The agent reads it at the start of every task and updates it in the same PR as any change to a feature.

Why in the repo and not in this skill: the map changes with every feature. The skill is stable rules; the map is versioned with the code, reviewed in PRs, and visible to every developer.

## Contents
1. The rule
2. If the map is missing or stale: discovery procedure
3. Template for `docs/platform-map.md`
4. Seed content (UNVERIFIED)
5. Keeping it true

---

## 1. The rule

At the start of every task:
1. Read `docs/platform-map.md`. Find the feature(s) and flow(s) your task touches.
2. Read the owning module(s) and the tests listed for that feature.
3. If the feature or flow is **not** in the map, or the map contradicts the code, do not guess. Run the discovery procedure for that flow (section 2), state what you found, and mark anything you could not confirm as `UNKNOWN - ask <owner>`.
4. At the end, update the map in the same change: new feature row, changed flow step, new module or util function, changed data ownership.

Honest limit: no agent (or person) understands every line of a large codebase. What this process guarantees is narrower and checkable: **no change is made without locating the feature, its flow, its owner, its tests, and its callers.**

## 2. Discovery procedure (build or verify a flow)

Do this for the flow you are about to change; do the whole product when creating the map for the first time.

1. **List entry points**: HTTP routes, the embeddable widget endpoints, background workers/jobs, CLI commands, scheduled tasks. Each is where a business flow starts.
2. **Trace each entry point end to end**: follow calls from the entry point through modules until the final side effect (response sent, row written, vector stored). Record each step as `module.function`, the data it reads/writes, and what happens on failure.
3. **Record configuration and flags** each step reads (setting name, unit, default, per-tenant or global).
4. **Record data stores** and which module owns each table/collection/file schema. Note any module reading another's storage directly: that is a boundary defect to log.
5. **Cross-check with tests**: for each feature, find its tests. No tests: record "unprotected".
6. **List what you could not determine** as `UNKNOWN` with a specific question and a suggested owner. Never fill a gap with a plausible guess: a wrong map is worse than a missing one because people trust it.
7. **Have a human who knows the business confirm the flows** before the map is marked verified. Code shows what happens, not what should happen.

## 3. Template for `docs/platform-map.md`

```
# Platform Map
Last verified: <date> by <name>     Status: draft | verified

## 1. What the product is
One paragraph: who uses it, what problem it solves, how it is delivered.

## 2. Actors
| Actor | What they do | Entry points they use |

## 3. Business flows
### Flow F1: <name>  (trigger -> outcome)
Trigger:            <who/what starts it>
Steps:              1. <module.function> - reads/writes <data> - on failure: <behavior>
                    2. ...
Config/flags:       <name (unit, default, per-tenant?)>
Data touched:       <stores and owners>
Tenant scoping:     <where enforced>
Failure/fallback:   <what the user sees; what is retried>
Tests:              <files / markers>
Open questions:     <UNKNOWN items>

## 4. Feature catalog
| ID | Feature | Owning module | Entry points | Flag | Tests | Status |

## 5. Module registry
| Module | Responsibility (one sentence) | Owner | Public API | Depends on |

## 6. Util registry
| Subpackage | Functions | Used by |

## 7. Data ownership
| Store / table / collection | Owner module | Readers (via public API only) | Schema/pipeline version |

## 8. Glossary
Terms with exact meanings and units (chunk, token, tenant, threshold, fallback, ...).

## 9. Change log
<date> <PR/ADR> <what changed in the map>
```

## 4. Seed content (UNVERIFIED)

Drawn from what has been described about this product. Use only as a starting checklist for discovery; every line must be confirmed against the code and the team before it is treated as fact.

**Product**: multi-tenant website chatbot platform, delivered to client websites through an embedded script tag; answers are generated from each client's own content stored in a vector database.

**Probable flows to verify**
- *Tenant onboarding*: create tenant, configure settings and flags, obtain the embed script.
- *Content ingestion*: discover/scrape client pages, clean and normalize, extract structured units (such as FAQ blocks) whole, chunk by tokens, embed (dense and sparse), write to the tenant's vector storage with a pipeline version.
- *Chat request*: widget sends a question, identify tenant, (optional query rewrite per flag), hybrid retrieval with fusion, thresholds, reranking, prompt assembly, LLM answer, cache read/write, explicit fallback policy when retrieval is weak.
- *Re-ingestion / content refresh*: re-run ingestion, invalidate that tenant's cache, keep pipeline versions consistent.
- *Evaluation set generation*: background job with persisted status producing labeled questions for quality measurement.

**Known sensitive areas** (see `product-invariants.md`): tenant isolation, thresholds and units, cache keys, pipeline versioning.

## 5. Keeping it true

- **Definition of Done includes the map**: a PR that adds/changes a feature, flow step, module, public API, util function, flag, or data owner updates the map. Reviewers check this.
- **Stale is a defect.** If while working you find the map wrong, fix it in your PR (or open a ticket with the exact discrepancy).
- **Every row has an owner.** Unowned rows rot first.
- Review the whole map on a fixed cadence (for example each release) and update "Last verified".
