# codebase-stewardship

An **Antigravity plugin** that enforces clean architecture, SOLID principles, LLD patterns, modular monolith structure, and rigorous testing standards across your codebase.

When this plugin is linked into your project's `.agents/plugins/` directory, Antigravity **automatically** discovers and loads all the skills and rules inside it — no extra configuration needed.

---

## Plugin Structure

```
codebase-stewardship/               ← This repo, cloned as a plugin
├── plugin.json                     ← Manifest: marks this as an Antigravity plugin
├── rules/
│   └── 01-architecture-mandate.md  ← Always-on architecture & SOLID rules
└── skills/
    └── codebase-stewardship/
        ├── SKILL.md                ← Skill entry point (loaded on demand)
        ├── references/             ← Deep reference docs used by the skill
        │   ├── platform-map.md
        │   ├── modular-monolith.md
        │   ├── testing-guide.md
        │   ├── novice-playbook.md
        │   ├── solid-in-practice.md
        │   ├── lld-workflow.md
        │   ├── product-invariants.md
        │   └── team-conventions.md
        ├── assets/                 ← Test templates & pytest config snippets
        └── scripts/
            └── devkit.py           ← scaffold, audit, and boundaries tooling
```

---

## How to Install (One-Time Setup Per Project)

**Option 1 — Clone directly**
```bash
cd your-project
git clone https://github.com/RSBalakrishnan/codebase-stewardship.git .agents/plugins/codebase-stewardship
```

**Option 2 — Git Submodule (Recommended for teams)**
```bash
cd your-project
git submodule add https://github.com/RSBalakrishnan/codebase-stewardship.git .agents/plugins/codebase-stewardship
git commit -m "chore: add codebase-stewardship plugin"
```

---

## How It Works After Installation

Once the plugin is in `.agents/plugins/codebase-stewardship/`, Antigravity automatically:

1. **Loads the rules** from `rules/` — the architecture mandate is active in every conversation.
2. **Registers the skill** from `skills/codebase-stewardship/SKILL.md` — the agent sees the skill name and description, and loads the full content (including all `references/`) only when the skill is triggered.

You don't need to copy any files or configure anything. Just prompt naturally:

- *"Review the current architecture and apply the stewardship rules."*
- *"Refactor this module according to the codebase stewardship guidelines."*
- *"Check if this new feature violates any of our stewardship principles."*
- *"Write tests for this module following the testing guide."*
