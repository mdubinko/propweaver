# PropWeaver Architecture Documentation

Welcome to PropWeaver's comprehensive architecture guides! This documentation explains the "why" behind PropWeaver's design, how it works, and how to work effectively with it (especially with AI tools).

## 📚 Quick Navigation

- **Want to understand PropWeaver's design?** → [ARCHITECTURE.md](ARCHITECTURE.md)
- **Want to understand why a specific decision was made?** → [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)
- **Using AI tools to work on PropWeaver?** → [AI_COLLABORATION.md](AI_COLLABORATION.md)
- **Updating or maintaining these guides?** → [WALKTHROUGH_WHYS.md](WALKTHROUGH_WHYS.md)

---

## 🎯 By Role

### Student Learning PropWeaver
1. Read ARCHITECTURE.md (start: Foundation + Three-Layer Architecture)
2. Read relevant sections of DESIGN_DECISIONS.md
3. Look at examples/ directory
4. Start contributing with AI_COLLABORATION.md as reference

### Contributor Adding Features
1. Read ARCHITECTURE.md fully
2. Read DESIGN_DECISIONS.md section on relevant decisions
3. Use AI_COLLABORATION.md for workflow with AI tools
4. Reference CLAUDE.md in repository root for project standards

### AI Tool Working on Codebase
1. Read ARCHITECTURE.md (particularly "Design for AI Collaboration")
2. Refer to AI_COLLABORATION.md for prompting patterns
3. Follow code review checklist in AI_COLLABORATION.md
4. Check CLAUDE.md for project standards

### Future Maintainer of These Docs
1. Read all four documents to understand scope
2. Use WALKTHROUGH_WHYS.md as your guide
3. Follow the maintenance schedule
4. Track improvements in TODO.md

---

## 📖 Document Overview

### ARCHITECTURE.md (≈4,000 words)
**What it is**: The main, comprehensive architecture guide

**Best for**: Understanding the "big picture" and how things fit together

**Key sections**:
- Foundation: What is PropWeaver?
- The Three-Layer Architecture
- Core Design Patterns
- Design for AI Collaboration (key section!)
- Thinking Like a Maintainer
- Key Design Decisions & Trade-offs

**Updates when**: Major architectural changes, fundamental principles change, new user-facing features

---

### DESIGN_DECISIONS.md (≈3,800 words)
**What it is**: Detailed exploration of individual design decisions

**Best for**: Understanding the reasoning and trade-offs of specific choices

**Structure of each decision**:
- The Decision (what was chosen)
- Why This Design (reasoning)
- The Trade-off (benefits vs. costs)
- Alternatives Considered
- When You Might Do It Differently

**Updates when**: A decision is reconsidered, new pattern emerges, trade-off changes

---

### AI_COLLABORATION.md (≈3,100 words)
**What it is**: Practical guide for working with AI tools on this codebase

**Best for**: Developers using AI assistants (Claude Code, ChatGPT, etc.)

**Key sections**:
- Why PropWeaver works well with AI tools
- Getting AI oriented (orientation sequence)
- Effective prompting patterns (6 patterns)
- Code review checklist for AI changes
- Iterative workflows (4 types)
- Common pitfalls and fixes
- Real worked example

**Updates when**: New effective patterns discovered, existing patterns stop working, new task types need guidance

---

### WALKTHROUGH_WHYS.md (≈2,000 words)
**What it is**: Meta-instructions for maintaining and updating the architecture guides

**Best for**: People responsible for keeping these documents current

**Key sections**:
- When to update each document
- Templates for common updates
- Consistency guidelines
- Maintenance schedule
- Evolution phases
- Feedback loop

**Updates when**: Documentation processes change, new update patterns emerge

---

## Notation

Throughout these architecture guides, code snippets are presented with specific conventions to aid understanding:

- **Usage Examples:** Code demonstrating how to use PropWeaver's public API will be prefixed with `## EXAMPLE` within the code block. These are typically self-contained and runnable by a user.

```python
## EXAMPLE
# This is a usage example
graph.add_node("User", name="Alice")
```

- **Internal Excerpts:** Code snippets from PropWeaver's internal implementation, used to illustrate architectural patterns or design decisions, will be surrounded by a line containing only `...`. These are not typically runnable on their own, but show patterns from within the source code.

```python
...
# This is an internal excerpt
class PropertyGraph:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._storage = StorageLayer(db_path)
...
```

<!-- AI_ASSISTANT_COMMENT: Use AI tools to maintain consistency in applying these notations across the documentation, and to ensure that excerpted and example code snippets remain consistent with the actual codebase. -->

---

## 📝 Contributing to These Docs

Found an issue? Want to improve the docs?

1. **Small improvement?** File a GitHub issue with "docs:" prefix
2. **Major update?** Check WALKTHROUGH_WHYS.md for update guidelines
3. **New pattern?** Add it to AI_COLLABORATION.md with examples
4. **Clarification?** Rewrite the section and explain the improvement

---

## 📞 Questions?

- **Architecture question?** → ARCHITECTURE.md
- **Why was something designed this way?** → DESIGN_DECISIONS.md
- **How do I work with AI tools here?** → AI_COLLABORATION.md
- **How do I update these docs?** → WALKTHROUGH_WHYS.md
- **Something else?** → Check README.md or ask your instructor

---

These are living documents. They're meant to evolve as the project and team evolve. Feedback and improvements are always welcome!