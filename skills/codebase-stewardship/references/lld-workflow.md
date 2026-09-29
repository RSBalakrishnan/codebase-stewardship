# LLD Workflow

Use for every non-trivial change (new module, new or changed interface, multi-layer change, persistence/schema, tenancy, retrieval or ingestion behavior). The purpose of the note is to expose wrong assumptions **before** code exists, when correcting them is cheap, and to give other developers a contract to build against in parallel.

Keep it to 1-2 pages. If it needs more, the change is probably several changes.

## Contents
1. LLD note template
2. How to fill it well
3. Design heuristics
4. LLD self-review checklist

---

## 1. LLD note template

```
# LLD: <change title>
Owner: <name>   Reviewers: <names>   Status: draft | approved | superseded

## 1. Problem and non-goals
What breaks or is missing, for whom. What this deliberately does not do.

## 2. Assumptions and invariants
Facts this design depends on (load, data size, ordering, ownership) - each
marked "verified" or "assumed". Invariants that must hold before and after.

## 3. Components and responsibilities
| Component | Single responsibility (one axis of change) | Depends on (abstractions) |

## 4. Interfaces and contracts
For each new/changed interface: signature, preconditions, postconditions,
errors raised, idempotency, thread/async safety.

## 5. Data model and persistence
Types, schema/payload fields, tenant key, indexes, migration and backfill plan,
what happens to existing data.

## 6. Behavior
Main-flow sequence (numbered steps or diagram) and at least three failure paths:
dependency down, bad input, partial failure. State what the caller observes.

## 7. Non-functional budget
Latency, memory, concurrency, cost per request/ingestion; how it degrades under
overload; limits and timeouts.

## 8. Alternatives considered
At least one real alternative with the trade-off that made you reject it.

## 9. Test plan
Unit (domain), contract (adapters), integration, and - for retrieval/ingestion -
the evaluation that would show quality did not regress.

## 10. Rollout and rollback
Feature flag / migration order / how to revert, and what is not revertible.
```

## 2. How to fill it well

- **Assumptions first.** Most design failures trace to an unstated assumption ("documents are small", "one tenant per collection", "the vendor never times out"). Mark each verified or assumed; assumed ones need a plan or a question to the team.
- **Responsibility column must be one axis.** If you write "and" in the cell, split the component or justify the coupling.
- **Contracts in prose plus types.** A signature does not state ordering, scoping, error behavior, or idempotency. Write those.
- **Failure paths are not optional.** A design without them describes only the demo. For each external call ask: what if it is slow, what if it fails after partial side effects, what if it is retried?
- **Alternatives must be genuine.** "Do nothing" and "the obviously worse option" do not count. State the trade-off, not a preference.
- **Test plan must be able to fail.** For each requirement name the test that would break if it were violated.

## 3. Design heuristics

**Find the volatility axes.** List what is likely to change independently (vendor, model, chunking policy, per-tenant behavior, scoring). Put seams there; keep stable policy on the inside.

**Draw the seam at I/O.** Network, DB, clock, randomness, and LLM calls sit behind abstractions so the logic around them is deterministic in tests.

**Make illegal states unrepresentable.** Use enums/state machines for lifecycles (ingestion job: pending -> running -> succeeded | failed) rather than boolean flag combinations. Transitions are defined in one place.

**Idempotency by default for background work.** Any job that can be retried or run twice must produce the same end state. Use natural keys or deterministic IDs.

**Prefer data flow over shared state.** Stages take typed input and return typed output. Hidden shared mutable state is what makes multi-developer changes collide.

**Separate policy from mechanism.** "What threshold" (policy, in config, per tenant if needed) vs "apply a threshold" (mechanism, in code).

**Design the failure mode you want.** Decide explicitly between fail-closed and fail-open for each dependency (e.g. if the reranker is down: skip it and log, or fail the request?). Write the decision and its reason.

**Bound everything.** Queue lengths, batch sizes, retries, in-memory collections, and payload sizes have explicit limits.

## 4. LLD self-review checklist

- [ ] Every component has one responsibility; no component named manager/helper/utils
- [ ] Dependencies point inward; no domain code imports infrastructure
- [ ] Every new abstraction meets one of the three justifications in SKILL.md
- [ ] Contracts state pre/postconditions and errors, not just signatures
- [ ] Tenant scoping is enforced at the boundary, not left to caller discipline
- [ ] Failure paths, timeouts, retries, and idempotency are specified
- [ ] Schema/payload changes have a migration and a re-ingestion decision
- [ ] Config values have names, units, defaults, and an owner
- [ ] There is a test that fails if each invariant is broken
- [ ] Rollback is defined; irreversible steps are called out
- [ ] All assumptions are marked verified or assumed
