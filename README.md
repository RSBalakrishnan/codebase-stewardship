# codebase-stewardship

This repository provides AI agent skills and rules for maintaining and stewarding a codebase. It is designed to be used by Antigravity (and other compatible AI coding agents) to enforce clean architecture, best practices, and consistent design patterns.

## How to Get This

You can integrate these stewardship skills into your own codebase by cloning this repository into your project's agent customization directory (`.agents`).

**Option 1: Clone directly**
```bash
# Navigate to your project's root directory
cd your-project

# Clone this repository into the workspace customizations root as a plugin
git clone https://github.com/RSBalakrishnan/codebase-stewardship.git .agents/plugins/codebase-stewardship
```

**Option 2: Add as a Git Submodule (Recommended)**
```bash
# Navigate to your project's root directory
cd your-project

# Add this repository as a git submodule
git submodule add https://github.com/RSBalakrishnan/codebase-stewardship.git .agents/plugins/codebase-stewardship
git commit -m "chore: add codebase-stewardship plugin for AI agent"
```

## How to Use It in Your Codebase

Once you have added this project to your `.agents/plugins/codebase-stewardship/` directory, your AI agent will automatically discover and load the stewardship skills and rules at the start of any new conversation.

To put it into action, simply open your AI agent and provide prompts such as:

- *"Review the current architecture and apply the stewardship rules."*
- *"Refactor this module according to the codebase stewardship guidelines."*
- *"Check if this new feature violates any of our stewardship principles."*

The agent will read the provided instructions and automatically apply the codebase maintenance practices defined in this repository.
