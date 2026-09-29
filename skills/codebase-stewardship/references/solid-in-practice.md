# SOLID in Practice

Read this when designing or reviewing a class hierarchy, an interface, or a service. Examples are Python; the reasoning is language-independent.

## Contents
1. SRP - Single Responsibility
2. OCP - Open/Closed
3. LSP - Liskov Substitution
4. ISP - Interface Segregation
5. DIP - Dependency Inversion
6. Where SOLID misleads
7. Quick review table

Each section gives: precise definition, how to detect a violation, the fix, and when NOT to apply it.

---

## 1. SRP - Single Responsibility

**Definition.** A module has one reason to change: one stakeholder or policy axis would independently request modifications to it. It is not "does one thing" (unfalsifiable) and not "is small".

**Detect.**
- Ask: who would request changes here? If the answers are independent (e.g. "search relevance tuning" and "billing rules"), it is two responsibilities.
- A change for one concern forces re-testing an unrelated concern.
- Merge conflicts repeatedly occur in the same file between developers working on unrelated features.
- The class needs mocks for many unrelated collaborators to be tested.

**Example violation.** One `ChatService.answer()` that rewrites the query, retrieves, reranks, assembles the prompt, calls the LLM, writes the cache, and logs analytics. Relevance tuning, prompt wording, cache policy, and telemetry all change it for different reasons.

**Fix.** Split by axis of change into stages with typed inputs/outputs (query rewrite, retrieval, rerank, prompt assembly, generation), and keep a thin orchestrator that only sequences them. The orchestrator's single responsibility is the sequence.

**When NOT to apply.** Do not split code that always changes together. Two functions that are edited in every change to the feature are one responsibility, and splitting them adds files without adding independence. Taken literally, SRP produces class explosion; use change-frequency evidence from history, not aesthetics.

---

## 2. OCP - Open/Closed

**Definition.** Behavior can be extended by adding code, not by editing tested existing code, for axes of variation that actually occur.

**Detect.** An `if/elif` or `match` on a type/provider/tenant-kind string that grows every time a variant is added, repeated in more than one place.

**Fix.** Strategy or registry behind a Protocol; the caller depends on the Protocol, and new variants register themselves.

```python
class Chunker(Protocol):
    def chunk(self, doc: Document) -> list[Chunk]: ...

CHUNKERS: dict[str, Chunker] = {"markdown": MarkdownChunker(), "faq": FaqChunker()}
```

**When NOT to apply.** Do not pre-build extension points for variation you have not seen. The first implementation is concrete; abstract at the second real variant, when you can see what actually varies. A guessed abstraction usually parameterizes the wrong axis and then must be undone. OCP is also unrealistic in absolute form: you cannot anticipate every axis, so some edits to existing code are normal.

---

## 3. LSP - Liskov Substitution

**Definition.** Any implementation of an abstraction can replace another without the caller being wrong. This is about **contracts** (preconditions no stronger, postconditions no weaker, same error behavior, invariants preserved), not signatures.

**Detect.**
- Caller code does `isinstance` checks or branches on concrete type.
- An override raises `NotImplementedError`, returns a degenerate value, or silently ignores an argument.
- A test fake behaves differently from the real adapter in ways production code relies on.

**Example violation.** `VectorStore.search(query, tenant_id, limit)` is contracted to return at most `limit` results, sorted by descending score, scoped to `tenant_id`. An in-memory fake that returns unsorted results, or ignores `tenant_id`, passes type checks yet makes every test that uses it lie.

**Fix and verification.** Write the contract as a reusable test suite parameterized over implementations and run it against the real adapter (in a container) and every fake:

```python
@pytest.fixture(params=[QdrantStore, InMemoryStore])
def store(request): ...

def test_results_are_tenant_scoped(store): ...
def test_results_sorted_desc_and_limited(store): ...
```

**When NOT to apply / limits.** Python's duck typing means the type checker will not catch behavioral violations; only contract tests do. Do not use inheritance just to share code (use composition); inheritance creates the LSP obligation.

---

## 4. ISP - Interface Segregation

**Definition.** A consumer should depend only on the operations it uses.

**Detect.** A service constructor takes the whole vendor client (or a 15-method interface) but calls two methods; test doubles need many stubbed methods irrelevant to the test.

**Fix.** Define narrow Protocols owned by the consumer.

```python
class Retriever(Protocol):
    def search(self, q: Query, tenant: TenantContext) -> list[Candidate]: ...
```

The Qdrant adapter implements `Retriever` (and separately `IngestionSink`); callers never see the vendor client.

**When NOT to apply.** Do not fragment an interface into one-method pieces when all consumers use all of it together. Segregate along consumer needs, not for its own sake.

---

## 5. DIP - Dependency Inversion

**Definition.** High-level policy does not depend on low-level detail; both depend on an abstraction, and the abstraction is owned by the high-level side (it is shaped by what the policy needs, not by what the vendor offers).

**Detect.**
- Application code imports a vendor SDK directly.
- Objects are constructed inside methods (`client = QdrantClient(...)`) or at import time; global singletons are used.
- Changing the LLM provider requires edits in several application modules.

**Fix.** Constructor injection; concrete choices only in the composition root.

```python
class AnswerUseCase:
    def __init__(self, retriever: Retriever, llm: LLMClient, clock: Clock): ...
```

**When NOT to apply.** Do not invert dependencies on stable, deterministic standard-library or pure-utility code (no interface for `json` or `math`). Invert at volatility and I/O boundaries. An interface per class is a smell (see the anti-over-engineering guard in SKILL.md).

---

## 6. Where SOLID misleads

- **It optimizes local structure, not system behavior.** A perfectly SOLID pipeline can still leak data across tenants or return poor answers. SOLID says nothing about correctness, performance, or security; those need their own checks (see `product-invariants.md`).
- **Indirection cost is real.** Every abstraction adds a hop for the reader and a place where behavior can hide. Measure abstraction by whether it reduced the cost of the last few real changes.
- **Unfalsifiable readings.** "Does one thing" and "open for extension" cannot be tested as stated. Use the detection questions above.
- **Unit-level focus hides boundary defects.** Most multi-developer defects come from mismatched assumptions between modules; contracts and boundary tests catch these more reliably than class-level purity.

## 7. Quick review table

| Symptom in a diff | Likely violated | First question to ask |
|---|---|---|
| Method with "and" in its natural description, many collaborators | SRP | Who independently requests changes to each part? |
| New `elif` for another provider/kind | OCP | Is this the second variant, and does the same switch exist elsewhere? |
| `isinstance` / `hasattr` in caller | LSP | What contract does the subtype break? |
| Fake in tests behaves differently from real adapter | LSP | Does a shared contract suite exist? |
| Vendor client passed through several layers | ISP / DIP | What is the minimal operation set the consumer needs? |
| `import qdrant_client` in application/domain code | DIP | Who owns this abstraction, and where is it wired? |
| New interface with one implementation and no I/O | Over-engineering | Which of the three justifications applies? |
