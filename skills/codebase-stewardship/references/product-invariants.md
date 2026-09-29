# Product Invariants: Multi-Tenant RAG Chatbot Platform

Read before touching ingestion, chunking, embedding, retrieval, reranking, prompt assembly, caching, tenant configuration, feature flags, or background jobs.

**Provenance and status.** These invariants are derived from the product's stated architecture (multi-tenant, script-tag embedded widget, per-client content in a vector database, hybrid dense+sparse retrieval with rank fusion, reranking, prompt assembly, semantic cache, background jobs, a small single-server deployment) and from defect classes already found in it (unit mix-ups, threshold misconfiguration, cache misconfiguration, premature splitting of structured content). Treat them as a starting contract for the team to confirm or amend by ADR; where the code contradicts one, the contradiction is a finding, not proof the invariant is wrong.

## Contents
1. Tenant isolation
2. Zero hardcoding
3. Feature flags
4. Units, thresholds, and pipeline versioning
5. Pipeline stage contracts
6. Cache correctness
7. Background jobs
8. External dependencies
9. Resource budget
10. Observability
11. Verifying retrieval changes

---

## 1. Tenant isolation (highest severity)

**Invariant.** No read or write path can touch another tenant's data.

**Why it is the top risk.** A cross-tenant leak exposes one customer's content to another's end users. It is a trust-ending incident for a commercial product, and it is invisible to functional tests that only use one tenant.

**Rules.**
- `tenant_id` is a **required** parameter (never optional, never defaulted) on every adapter method that reads or writes tenant data, carried in a `TenantContext` object.
- Scoping is enforced **inside the adapter** (filter or collection selection applied there), not left to each caller to remember. The adapter refuses calls without a tenant.
- Cache keys, job records, log fields, and uploaded/scraped content all include the tenant identifier.
- Tenant identity is derived from the authenticated/embedded-site credential server-side, never from a client-supplied field alone.

**Verify.** A cross-tenant test in the contract suite: ingest distinct content for tenants A and B, query as A with text that best matches B's content, assert zero B results. Run against every store implementation.

## 2. Zero hardcoding

**Invariant.** Client-specific behavior (page discovery, navigation, content classification, wording) comes from data and configuration, never from code branches keyed on a client, domain, or specific page.

**Review test.** "Does onboarding client N+1 require a code change?" If yes, it is a defect. Also grep for tenant names, domains, and literal URLs in non-test code.

**Trade-off to acknowledge.** Dynamic, data-driven behavior is harder to debug than a hardcoded branch. The mitigation is observability (log which rule/score drove a decision), not reintroducing hardcoding.

## 3. Feature flags

- Per-tenant flags resolve in **one** place (a resolver that takes `TenantContext` and returns typed settings), not as scattered `if tenant == ...` or ad hoc config reads.
- New behavior that changes retrieval or answers ships behind a flag that defaults **off**, and is enabled per tenant after evaluation.
- Flags have an owner and a removal condition; a permanent flag is a fork of the product.

## 4. Units, thresholds, and pipeline versioning

- Sizes carry units in the name and type: `chunk_size_tokens`, not `chunk_size`. Count tokens with the **same tokenizer family the embedding/LLM path assumes**; character counts are not a substitute and produce systematically wrong chunk sizes.
- Score thresholds are config values with a documented scale and meaning. Scores from different stages (dense similarity, fused rank score, reranker score) are **not comparable**; a threshold belongs to exactly one stage. Changing the retrieval method invalidates existing thresholds.
- Anything that changes what is stored (chunking policy, header handling, embedding model, sparse encoder, payload schema) changes the meaning of existing vectors. Store a `pipeline_version` on stored points/payloads, and treat a change as: ADR, migration or re-ingestion plan, evaluation before/after. Silent mixing of versions in one collection makes results unexplainable.

## 5. Pipeline stage contracts

Model the request path as typed stages, each testable alone:

```
Query -> (rewrite?) -> Retrieve -> Fuse -> Rerank -> Assemble prompt -> Generate -> Post-process
```

- Each stage is a function/class over immutable typed input and output. Stages do not reach into each other's internals or share hidden mutable state.
- Decide once, in the owning stage, where information lives. Example: whether a section heading is part of the embedded chunk text or only metadata is a **chunker** decision with retrieval consequences; downstream stages must not compensate for it.
- Structured units (e.g. an FAQ question with its answer) are extracted whole **before** generic size-based splitting; splitting first destroys the unit and cannot be repaired downstream.
- Fallback behavior (e.g. going to an external search when retrieval is weak) is an explicit policy with a stated trigger condition, config-driven, logged, and tested at both sides of the threshold. It is not an implicit side effect of a low score.

## 6. Cache correctness

- Cache key includes: `tenant_id`, `pipeline_version`, and the normalized query (plus any flag that changes the answer).
- Semantic (similarity-based) caching has a false-hit cost: a wrong cached answer is served with confidence. The similarity threshold is a documented config value validated on labeled near-duplicate and near-miss pairs, and it is conservative by default.
- Re-ingestion of a tenant's content invalidates that tenant's cache. Every cache entry has a TTL.
- **Verify** with tests: same question different tenant -> miss; content re-ingested -> miss; near-miss question -> miss.

## 7. Background jobs (ingestion, evaluation generation, re-indexing)

- A job has a persisted status state machine (for example pending -> running -> succeeded | failed), with transitions defined in one place, and a stored error summary on failure.
- Jobs are **idempotent** and safe to retry; use deterministic point IDs / upserts so a rerun does not duplicate content.
- Jobs are bounded: timeout, retry cap with backoff, batch sizes from config.
- The request path never blocks on a long job; it returns a job identifier, and status is queryable.

## 8. External dependencies (LLM, scraper, vector store, reranker)

- Every call: explicit timeout, retry only if idempotent (capped, with backoff and jitter), circuit breaker or equivalent for repeated failure.
- Decide fail-open vs fail-closed per dependency and record why (e.g. reranker down: skip reranking and log vs return an error).
- Translate vendor exceptions to domain exceptions in the adapter; callers never catch vendor types.
- Scraped or retrieved content is **untrusted input**. It can contain instructions aimed at the model. Keep it clearly delimited in the prompt, never let it alter system instructions or tool permissions, and never echo secrets into prompts.

## 9. Resource budget

The deployment target is small (a single low-memory server has been described). Therefore:
- No unbounded in-memory collections of chunks/embeddings; process ingestion in bounded batches or streams.
- Concurrency (workers, parallel embedding/LLM calls) comes from config and is sized against a measured memory ceiling, not guessed.
- Any change that increases memory or per-request cost per tenant states the estimate in the LLD and is checked against the budget. Scaling the machine is a decision to record, not a way to skip the estimate.

## 10. Observability

- Every log line and metric on request and job paths carries `tenant_id` and a request/job id.
- Log per-stage timings and the retrieval decision inputs (candidate counts, scores at each stage, whether fallback triggered) so a bad answer can be diagnosed after the fact.
- Do not log secrets, credentials, or full end-user messages by default.

## 11. Verifying retrieval changes

Unit tests do not show that answers got better or worse. For any change to chunking, embedding, fusion, thresholds, reranking, rewriting, or prompts:

1. Maintain a labeled evaluation set per representative tenant (question, expected source chunk/answer).
2. Report metrics before and after on the same set: retrieval hit rate at k, and answer correctness by whatever grading method the team has validated.
3. Report failures by category (no result, wrong result, right result ranked low, unnecessary fallback), not just an aggregate, because an average can improve while a category regresses.
4. Roll out behind a flag, per tenant, with the ability to revert.

A change to this pipeline with no before/after numbers is an unverified change, whatever the unit tests say.
