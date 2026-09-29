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

## 3. Required Architectural Layers (Technology-Agnostic)

The folder/file naming convention varies by framework and language — **that is expected and correct**. What must NEVER vary is the **separation of concerns** between these four layers:

| Layer | Responsibility | Must NOT contain |
| :--- | :--- | :--- |
| **Domain / Core** | Business entities, value objects, domain rules, abstract interfaces (ports) | I/O, framework imports, database calls |
| **Application / Use Cases** | Orchestrates domain objects to fulfil a single business use case | Direct DB calls, HTTP logic, UI concerns |
| **Infrastructure / Adapters** | Implements domain ports: DB repos, external API clients, file I/O | Business rules, domain logic |
| **Presentation / Delivery** | HTTP routes, CLI handlers, event consumers — maps I/O to use cases | Business logic, DB queries |

**Adapt the naming to your stack:**

- **Python + FastAPI** → `domain/`, `application/`, `infrastructure/`, `presentation/`
- **Node.js + Express** → `models/`, `services/`, `repositories/`, `controllers/`
- **Spring Boot (Java)** → `entity/`, `service/`, `repository/`, `controller/`
- **Django** → `models/`, `services/`, `selectors/`, `views/`
- **Next.js (Frontend)** → `domain/`, `services/` or `api/`, `hooks/`, `components/`, `app/` or `pages/`

**The non-negotiable rules regardless of naming:**

1. **Domain layer has zero dependencies** on infrastructure, frameworks, or external libraries.
2. **Business logic lives in Domain/Application** — never in routes, controllers, or views.
3. **Dependency direction is always inward**: Presentation → Application → Domain ← Infrastructure.
4. **Infrastructure depends on Domain abstractions** (interfaces/ports), not the other way around.
5. **Each bounded context / feature module** is self-contained with its own layers. Avoid cross-module direct imports; go through public APIs.

---

## 4. Verification & Testing Protocol

1. **Unit Test Co-location**: For every new use case or domain service, write dedicated unit tests using mock/in-memory port adapters.
2. **Regression Prevention**: Before declaring any task complete, run the project's automated test suite. **100% test pass rate must be preserved at all times.**
