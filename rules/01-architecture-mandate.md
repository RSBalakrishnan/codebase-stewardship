# Default Engineering Mandate: LLD, SOLID, DRY, KISS Principles, Clean Code & Architecture

> **SCOPE**: Applies globally as the **DEFAULT INSTRUCTION** for the Antigravity Agent across ALL workspaces, repositories, and projects.

---

## 1. The Cardinal Rule: Zero Unsolicited Migration (User Consent Mandate)

```
   ┌────────────────────────────────────────────────────────────────────────┐
   │                                                                        │
   │   DO NOT MIGRATE, RE-ARCHITECT, OR REWRITE EXISTING CODEBASES WITHOUT │
   │   EXPLICIT USER INSTRUCTION OR PRIOR APPROVAL.                         │
   │                                                                        │
   └────────────────────────────────────────────────────────────────────────┘
```

1. **Leave Working Legacy Code Untouched**:
   - Existing codebases or legacy working scripts must **NEVER** be refactored, migrated, or cleaned up unprompted, even if they appear clumsy, monolithic, or non-compliant with clean architecture.
   - If existing code is functional, it must be preserved as-is.

2. **Explicit User Trigger Required**:
   - You may **ONLY** migrate or refactor existing code into clean architecture if the user **explicitly requests it** (e.g., *"Migrate this service to clean architecture"*, *"Refactor this module using SOLID"*).

3. **Surgical Bug Fixing / Patching**:
   - When asked to fix a bug or add a minor hook into an existing legacy file, keep the change **minimal, surgical, and localized**.
   - Do **NOT** use bug fixes as an opportunity to perform widespread refactorings of surrounding files without user consent.

---

## 2. The Core Mandate: Every NEW Implementation Must Follow LLD, SOLID, DRY & KISS

While existing legacy code is protected from unsolicited migration, **EVERY NEW PIECE OF CODE** (new feature, new service, new endpoint, new use case, new class, new component, or new module) **MUST STRICTLY ADHERE** to the following principles:

---

### A. SOLID Principles

| Principle | Meaning & Requirement | Anti-Pattern to Strictly Avoid |
| :--- | :--- | :--- |
| **S — Single Responsibility (SRP)** | Every class, module, and function must have **one, and only one, reason to change**. Separate business orchestration from data parsing, network calls, and database persistence. | Monolithic "god objects" or 500+ line utility classes that handle subprocesses, networking, parsing, and SQL all at once. |
| **O — Open-Closed (OCP)** | Code must be **open for extension, but closed for modification**. Use interfaces, abstract base classes, registries, and the Strategy Pattern so new capabilities can be plugged in without modifying existing code. | Sprawling `if/elif/switch` branches checking for frameworks, languages, or types inside core business workflows. |
| **L — Liskov Substitution (LSP)** | Derived classes or adapter implementations must be completely substitutable for their base interfaces without altering correctness. | Subclasses throwing `NotImplementedError` for methods in the interface, or violating contract invariants. |
| **I — Interface Segregation (ISP)** | Create small, focused, client-specific interfaces (ports). Clients should never depend on methods they do not call. | Fat interfaces with 30+ disparate methods covering auth, database, file system, and network operations. |
| **D — Dependency Inversion (DIP)** | High-level business logic must depend **exclusively on domain abstractions (interfaces/ports)**, NEVER on low-level technical details (raw SQL, concrete ORMs, third-party libraries). | Use cases directly importing SQLAlchemy models, raw database connections, or concrete vendor SDKs. |

---

### B. DRY & KISS Principles

| Principle | Meaning & Requirement | Anti-Pattern to Strictly Avoid |
| :--- | :--- | :--- |
| **DRY — Don't Repeat Yourself** | Every piece of knowledge, logic, or business rule must have a **single, unambiguous, authoritative representation** in the codebase. Extract reusable domain services, shared utilities, common schemas, or base classes when logic is duplicated across multiple components. | Copy-pasting identical validation logic, SQL queries, regex patterns, or AST parsing code into multiple endpoints/files. |
| **KISS — Keep It Simple, Stupid** | **Simplicity is the primary engineering goal.** Systems and functions must be designed to be straightforward, obvious, and easy to read. Write direct, self-explanatory code. Favor composition over convoluted inheritance hierarchies, and never introduce premature abstractions. | Over-engineering simple features with gratuitous layers, creating 10-layer abstractions for trivial operations, or writing "clever"/obscure one-liners. |

---

### C. Required Low-Level Design (LLD) Patterns

When implementing new logic, proactively select and apply appropriate GoF design patterns:

| Pattern | Where & When to Use | Reference Implementation |
| :--- | :--- | :--- |
| **Strategy Pattern** | Language/framework parsers, test generators, diff algorithms. | `IExtractor` + `SpringControllerExtractor`, `FastApiExtractor` |
| **Factory / Registry Pattern** | Dynamically resolving strategies by project markers (`pom.xml`, `package.json`, etc.). | `ExtractorFactory` in `src/infrastructure/parsers/factory.py` |
| **Repository Pattern** | All database read/write operations. Business logic never writes raw SQL. | `SqlCanonicalRepository`, `SqlProjectRepository` |
| **Adapter Pattern** | Wrapping third-party packages (Tree-sitter, Bedrock LLM, Fernet encryption, Git CLI). | `BedrockClient`, `TreeSitterCSTAdapter` |
| **DTO (Data Transfer Object)** | Passing immutable data across application boundaries (HTTP -> Application -> Domain). | `IntrospectionRequestDTO`, `CreateProjectDTO` |
| **Composite Upsert** | Persisting entities with deduplication on unique business keys. | `SqlCanonicalRepository.save_all` |
| **Ports & Adapters (Hexagonal)** | Decoupling core domain entities & ports from external technical adapters. | Domain ports (`interfaces.py`) + Infrastructure adapters (`repositories.py`) |
| **Facade Pattern** | Providing a clean, unified interface to complex subsystems when invoked by external boundaries. | Application Use Case orchestrators |

---

### D. Clean Code Standards

1. **Domain-Expressive Naming**:
   - Use clear, intention-revealing names for classes, functions, and variables.
   - Avoid cryptic abbreviations, generic names (`data`, `temp`, `item`, `res`), or misleading prefixes.
2. **Small, Focused Functions**:
   - Functions should do one thing and do it well (aim for under 30–40 lines).
   - Functions should either perform an action or answer a query, never both (Command-Query Separation).
3. **Defensive Typing & Strict Contracts**:
   - **Python**: Use Python type hints (`typing`, `Pydantic`) for all function signatures, parameters, and return types.
   - **TypeScript**: Use strict interfaces/types; ban the use of `any`.
4. **Explicit Domain Exceptions**:
   - Define custom domain exceptions (e.g., `EntityNotFoundException`, `ValidationException`).
   - Never use bare `except:` or swallow exceptions silently.
5. **Zero Magic Values**:
   - Extract magic numbers, status strings, and default configurations into named constants or Enums.

---

## 3. Standard Layered File Structure

### For Backend Projects:
New features must be organized by **Bounded Context** under `src/modules/<context>/` following the 4-layer Hexagonal structure:

```
src/modules/<bounded_context>/
├── domain/                  # PURE DOMAIN LAYER (Zero external dependencies)
│   ├── models.py            # Domain Entities, Value Objects (Pydantic / Dataclasses)
│   └── interfaces.py        # Ports: Abstract Base Classes (ABC) defining contracts
├── application/             # APPLICATION / USE CASE LAYER (Business Orchestration)
│   ├── dtos.py              # Input / Output Data Transfer Objects
│   └── *_use_case.py        # Single-purpose orchestrators; depends ONLY on domain ports
├── infrastructure/          # ADAPTERS LAYER (Technical Details & External Services)
│   ├── orm_models.py        # SQLAlchemy ORM models (isolated from domain entities)
│   ├── repositories.py      # Repository implementations of domain ports
│   └── adapters/            # External API clients, AST parsers, LLM drivers, etc.
└── presentation/            # PRESENTATION / DELIVERY LAYER (HTTP & API)
    ├── schemas.py           # FastAPI request / response Pydantic schemas
    └── *_routes.py          # FastAPI APIRouter endpoints; invokes use cases via DI
```

### For Frontend Projects:
New frontend features must follow strict separation of presentation and business logic:

```
src/
├── types/ or domain/        # Domain models, API contract interfaces, Enums
├── services/ or api/        # Typed API clients & transport adapters
├── hooks/                   # Custom hooks encapsulating state, effects, and business workflows
├── components/              # Single-responsibility, reusable UI components (< 150 lines)
│   ├── common/              # Shared design system components (buttons, modals, inputs)
│   └── <feature>/           # Feature-specific composite components
└── views/ or pages/         # Page-level route views (coordinates components & hooks)
```

---

## 4. Verification & Testing Protocol

1. **Unit Test Co-location**:
   - For every new use case or domain service, write dedicated unit tests verifying edge cases and business rules using mock/in-memory port adapters.
2. **Regression Prevention**:
   - Before declaring any task complete, run the project's automated test suite.
   - **100% test pass rate must be preserved at all times.**
