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
   - Existing codebases or legacy working scripts must **NEVER** be refactored, migrated, or cleaned up unprompted.
   - If existing code is functional, it must be preserved as-is.

2. **Explicit User Trigger Required**:
   - You may **ONLY** migrate or refactor existing code into clean architecture if the user **explicitly requests it**.

3. **Surgical Bug Fixing / Patching**:
   - When asked to fix a bug or add a minor hook into an existing legacy file, keep the change **minimal, surgical, and localized**.
   - Do **NOT** use bug fixes as an opportunity to perform widespread refactorings of surrounding files.

---

## 2. The Core Mandate: Every NEW Implementation Must Follow LLD, SOLID, DRY & KISS

### A. SOLID Principles

| Principle | Meaning & Requirement | Anti-Pattern to Strictly Avoid |
| :--- | :--- | :--- |
| **S — Single Responsibility (SRP)** | Every class, module, and function must have **one, and only one, reason to change**. | Monolithic "god objects" that handle subprocesses, networking, parsing, and SQL all at once. |
| **O — Open-Closed (OCP)** | Code must be **open for extension, but closed for modification**. Use interfaces, abstract base classes, registries, and the Strategy Pattern. | Sprawling `if/elif/switch` branches checking for frameworks or types inside core business workflows. |
| **L — Liskov Substitution (LSP)** | Derived classes must be completely substitutable for their base interfaces without altering correctness. | Subclasses throwing `NotImplementedError` for methods in the interface, or violating contract invariants. |
| **I — Interface Segregation (ISP)** | Create small, focused, client-specific interfaces. Clients should never depend on methods they do not call. | Fat interfaces with 30+ disparate methods covering auth, database, file system, and network operations. |
| **D — Dependency Inversion (DIP)** | High-level business logic must depend **exclusively on domain abstractions (interfaces/ports)**, NEVER on low-level technical details. | Use cases directly importing SQLAlchemy models, raw database connections, or concrete vendor SDKs. |

### B. DRY & KISS Principles

| Principle | Meaning & Requirement | Anti-Pattern to Strictly Avoid |
| :--- | :--- | :--- |
| **DRY — Don't Repeat Yourself** | Every piece of logic must have a **single, unambiguous, authoritative representation** in the codebase. | Copy-pasting identical validation logic, SQL queries, or parsing code into multiple files. |
| **KISS — Keep It Simple, Stupid** | **Simplicity is the primary engineering goal.** Write direct, self-explanatory code. | Over-engineering simple features with gratuitous layers or premature abstractions. |

### C. Required LLD Patterns

| Pattern | Where & When to Use |
| :--- | :--- |
| **Strategy Pattern** | Language/framework parsers, test generators, diff algorithms. |
| **Factory / Registry Pattern** | Dynamically resolving strategies by project markers. |
| **Repository Pattern** | All database read/write operations. Business logic never writes raw SQL. |
| **Adapter Pattern** | Wrapping third-party packages (Tree-sitter, LLMs, Git CLI). |
| **DTO (Data Transfer Object)** | Passing immutable data across application boundaries. |
| **Ports & Adapters (Hexagonal)** | Decoupling core domain entities & ports from external technical adapters. |
| **Facade Pattern** | Providing a clean, unified interface to complex subsystems. |

### D. Clean Code Standards

1. **Domain-Expressive Naming**: Use clear, intention-revealing names. Avoid `data`, `temp`, `item`, `res`.
2. **Small, Focused Functions**: Aim for under 30–40 lines. Command-Query Separation.
3. **Defensive Typing**: Python → type hints + Pydantic. TypeScript → strict interfaces, no `any`.
4. **Explicit Domain Exceptions**: Define custom exceptions. Never use bare `except:` or swallow silently.
5. **Zero Magic Values**: Extract all magic numbers, status strings, and config into named constants or Enums.

---

## 3. Standard Layered File Structure

### For Backend Projects (Hexagonal / Clean Architecture):
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

1. **Unit Test Co-location**: For every new use case or domain service, write dedicated unit tests using mock/in-memory port adapters.
2. **Regression Prevention**: Before declaring any task complete, run the project's automated test suite. **100% test pass rate must be preserved at all times.**
