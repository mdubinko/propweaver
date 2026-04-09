# Walkthrough Whys: Meta-Instructions for Updating Architecture Guides

This document is for future maintainers (including AI tools working on this codebase) who need to update or extend the architecture guides. It explains:

1. **Why these documents exist** - The intent behind creating them
2. **How to update them** - When and how to modify each document
3. **What triggers updates** - Signs that a document needs refreshing
4. **How to maintain consistency** - Keeping all guides aligned

---

## Overview of the Architecture Guides

We created three living documents to help students and contributors understand PropWeaver:

### ARCHITECTURE.md (The Main Guide)

**Purpose**: Comprehensive overview of PropWeaver's design and how it works

**Content**:
- Foundation: What PropWeaver is and why it exists
- Three-layer architecture explanation
- Core design patterns (proxies, lazy evaluation, etc.)
- Architecture by layer (detailed exploration of each)
- Design for AI collaboration (key differentiator)
- Thinking like a maintainer (how to approach problems)
- Key design decisions (trade-offs)

**Audience**: Everyone - students, contributors, AI tools

**Update Triggers**:
- Major architectural changes (new layer, removed layer, fundamental pattern change)
- New user-facing API feature
- Significant design decision made (document it here)

**Note**: This document emphasizes the "why" and principles, not implementation details.

### DESIGN_DECISIONS.md (The Deep Dives)

**Purpose**: Detailed exploration of individual design decisions

**Content**:
- For each major decision:
  - The decision (what was chosen)
  - Why (reasoning, benefits)
  - Trade-offs (benefits and costs)
  - Alternatives considered
  - When you might do it differently

**Audience**: Developers who want to understand rationale before extending

**Update Triggers**:
- A design decision is significantly reconsidered
- A new design pattern emerges (add a new section)
- A trade-off changes (e.g., we now value performance over flexibility)
- An alternative becomes viable (document why we didn't choose it)

**Note**: This document is thorough but not the place for implementation details.

### AI_COLLABORATION.md (The Workflow Guide)

**Purpose**: Practical guide for working with AI tools on this codebase

**Content**:
- Why PropWeaver works well with AI tools
- How to get AI oriented (sequence of steps)
- Effective prompting patterns
- How architecture helps and constrains AI
- Code review for AI-generated changes
- Development workflows
- Common pitfalls and fixes
- Using CLAUDE.md and TODO.md
- Real example

**Audience**: People using AI tools to develop PropWeaver

**Update Triggers**:
- You discover a new effective pattern for AI collaboration
- An existing pattern stops working
- A new type of task (refactoring, bug fixing, etc.) needs guidance
- Pitfalls change (new mistakes emerge, old ones disappear)
- CLAUDE.md changes significantly

**Note**: This is the most practical, evolving document. Update it as you learn what works.

---

## When to Update Each Document

### ARCHITECTURE.md

**Update if**:
- The three-layer structure changes
- A fundamental design principle changes
- New core concepts are introduced
- The approach described in CLAUDE.md significantly changes

**Don't update for**:
- New features (those go in README or examples)
- Bug fixes (unless they change architecture)
- Small API additions
- Documentation changes

**How to Update**:
1. Identify which section(s) are affected
2. Update the explanation of why/how
3. If adding a new pattern, add it to "Core Design Patterns" section
4. Run the document by a colleague or AI tool: "Is this still accurate?"

### DESIGN_DECISIONS.md

**Update if**:
- A new design decision is made (add a new section)
- Trade-offs change significantly
- You decide to redo a decision (update that section)
- New alternatives become viable

**Don't update for**:
- Implementation details changing
- Bug fixes
- Performance improvements that don't change the decision

**How to Update**:
1. For new decision: Copy the template at the bottom
2. For existing decision: Update "Why", "Trade-offs", or "When you might do differently"
3. Review the decision with team members
4. Add a note in TODO.md if this changes future development

### AI_COLLABORATION.md

**Update if**:
- You find a new effective prompting pattern
- An existing pattern stops working
- You discover a new pitfall
- CLAUDE.md changes

**Don't update for**:
- Feature additions (unless they change how you work with AI)
- Bug fixes

**How to Update**:
1. Identify which section(s) are affected
2. Add new pattern/pitfall with explanation
3. Test the pattern/pitfall with AI before documenting
4. Include a real example if possible

---

## Templates for Common Updates

### Template: Adding a New Core Design Pattern to ARCHITECTURE.md

```markdown
### Pattern X: [Pattern Name]

Instead of [what people might do], PropWeaver uses [this approach]:

[Code example showing the pattern]

**Why?**
- [Benefit 1]
- [Benefit 2]
- [Benefit 3]

**Trade-off**: [What you're giving up for this approach]

**How it works**: [Brief explanation of how it actually works]
```

### Template: Adding a New Design Decision to DESIGN_DECISIONS.md

```markdown
## Decision N: [Decision Title]

### The Decision

[What was chosen]

[Schema/code example showing the decision]

### Why This Design

[Explain the reasoning]

**Benefits**:
- ✅ [Benefit 1]
- ✅ [Benefit 2]

**Costs**:
- ❌ [Cost 1]
- ❌ [Cost 2]

### When You Might Do It Differently

[Discuss alternatives, when they'd be better]

### Related Decisions

[How this decision enables or depends on other decisions]
```

### Template: Adding a New Prompting Pattern to AI_COLLABORATION.md

```markdown
### Pattern N: [Pattern Name]

**Good Prompt**:
[Example prompt]

**Why This Works**:
- [Reason 1]
- [Reason 2]

**When to Use**:
[Situations where this pattern is useful]

**Common Mistakes**:
[What people get wrong about this pattern]
```

### Template: Adding a New Pitfall to AI_COLLABORATION.md

```markdown
### Pitfall N: "[Brief description]"

**The Problem**:
[What goes wrong]

[Example of the problem]

**The Fix**:
[How to avoid it]

[Example of the fix]

**Why This Happens**:
[Explanation of why AI or humans might do this]
```

---

## Consistency Across Documents

These documents should be aligned. Here's how to maintain consistency:

### Cross-References

When a document refers to another, use clear links:

**In ARCHITECTURE.md**:
```
For deeper dives on specific decisions, see DESIGN_DECISIONS.md.

Specific decision details:
- [Lazy evaluation](#lazy-evaluation--queryspec)
  (see DESIGN_DECISIONS.md: Lazy Evaluation & QuerySpec)
```

**In AI_COLLABORATION.md**:
```
The architecture constrains how AI can modify code (see ARCHITECTURE.md: The Three-Layer Architecture).
```

### Synchronized Concepts

When a concept is in multiple documents, ensure they tell the same story:

**Example: Three-Layer Architecture**
- ARCHITECTURE.md: Explains the three layers in detail
- DESIGN_DECISIONS.md: Explains why we have three layers
- AI_COLLABORATION.md: Explains how layers help AI stay focused

Check: Do all three documents agree on what the layers are?

### Update Checklist

When making a significant change:

- [ ] Update the primary document where the change belongs
- [ ] Check if other documents need updates (cross-references)
- [ ] Verify examples are consistent across documents
- [ ] Run the documents by someone (human or AI) for alignment
- [ ] Update TODO.md if this changes the approach
- [ ] Create a commit explaining the documentation change

---

## What NOT to Document Here

These architecture guides are not the place for:

❌ **Implementation Details**
- Don't document "StorageLayer has a _execute_query() method"
- Do document "Storage layer executes query plans"

❌ **API Reference**
- That's in README.md and code docstrings
- Not in architecture guides

❌ **How-To Guides for Users**
- Examples: "How to create a node", "How to query properties"
- That's in README.md and examples/

❌ **Installation Instructions**
- That's in README.md

❌ **Change History**
- That's in git commits and CHANGELOG (when we have one)

❌ **Bugs & Known Issues**
- That's in GitHub issues and TODO.md

---

## Evolution of These Documents

These documents should evolve as PropWeaver evolves:

### Phase 1: Initial Creation (Done)
- Created comprehensive ARCHITECTURE.md
- Created DESIGN_DECISIONS.md with all current decisions
- Created AI_COLLABORATION.md with patterns and workflows

### Phase 2: Using the Guides (Now)
- Students/contributors use these for learning
- AI tools reference these for understanding code
- Team members reference these when making decisions

### Phase 3: Iterative Improvement (Ongoing)
- Update guides based on experience
- Add new patterns as they emerge
- Remove/consolidate sections that don't help
- Test guide effectiveness with new people

### Phase 4: Refinement (Future)
- Stabilize on the most effective explanations
- Possibly extract into separate documents by audience
- Consider automated checking (are our design decisions being followed?)

---

## How AI Tools Should Update These Documents

If an AI tool is assigned to update these documents:

**Guidelines**:
1. Read the entire document before proposing changes
2. Check consistency with other documents
3. Preserve the voice and style (explain the why, not the what)
4. Use examples sparingly (one good example per concept)
5. Include the reasoning for changes in commit message

**Red Flags**:
- 🚩 Adding implementation details (this belongs in code, not docs)
- 🚩 Removing sections without checking cross-references
- 🚩 Changing the structure without discussion
- 🚩 Adding content that belongs elsewhere (API docs, README, etc.)
- 🚩 Removing important context or examples

**Good Changes**:
- ✅ Adding a new design decision (with full context)
- ✅ Adding a new prompting pattern (with working examples)
- ✅ Updating trade-offs based on experience
- ✅ Clarifying confusing explanations
- ✅ Adding cross-references for consistency

---

## Reviewing Architecture Guide Changes

When reviewing changes to these documents:

**Checklist**:
- [ ] Does it belong in this document? (Not in README, not implementation details)
- [ ] Is it consistent with other documents?
- [ ] Are examples correct and helpful?
- [ ] Is the explanation clear? (Could a newcomer understand?)
- [ ] Do cross-references work?
- [ ] Is it accurate? (Have you verified this is how the code works?)

**Questions to Ask**:
- Is this explaining why or explaining what?
- Could this be clearer with an example?
- Does this align with the philosophy stated in CLAUDE.md?
- Would a student understand this without asking questions?
- Does this help AI tools collaborate better on this codebase?

---

## Maintenance Schedule (Recommended)

**Quarterly**:
- Review AI_COLLABORATION.md for new patterns/pitfalls
- Check that examples still work

**Semi-Annually**:
- Review all guides for accuracy
- Update DESIGN_DECISIONS.md if any decisions have changed
- Check for consistency across documents

**Annually**:
- Major review of ARCHITECTURE.md
- Assess if structure is still effective
- Consider additions/removals

---

## Questions to Revisit

When updating these documents, reconsider these questions:

1. **Audience**: Are we still targeting students and contributors? Have priorities changed?

2. **Depth**: Is the level of detail right? Too much explanation? Not enough?

3. **AI Collaboration**: Are we still prioritizing AI collaboration? Has something changed about how we work?

4. **Patterns**: Have new patterns emerged that should be documented? Old patterns become obsolete?

5. **Trade-offs**: Have our trade-offs changed? Do we still value flexibility over performance? Clarity over brevity?

6. **Effectiveness**: Are these documents helping people? How do we know?

---

## Feedback Loop

Help future maintainers by:

1. **Noting what worked**: When a guide helps someone understand something quickly, note it
2. **Noting what didn't**: When a guide was confusing or incomplete, file an issue
3. **Suggesting improvements**: "This section would be clearer if..."
4. **Adding examples**: "I found the architecture helps people understand this feature..."
5. **Reporting gaps**: "The guides don't explain how to..."

Update TODO.md with discoveries:

```markdown
## Documentation Findings

- [ ] ARCHITECTURE.md section on proxies is confusing, needs clarification
- [ ] AI_COLLABORATION.md missing prompting pattern for refactoring
- [ ] DESIGN_DECISIONS.md should add "Performance" as a decision
```

---

## Summary

These documents are living, evolving guides:

- **ARCHITECTURE.md**: The foundational reference
- **DESIGN_DECISIONS.md**: Deep dives into specific choices
- **AI_COLLABORATION.md**: Practical workflows and patterns
- **WALKTHROUGH_WHYS.md**: This meta-guide for updating them

Together, they form a comprehensive explanation of PropWeaver's design. Keep them aligned, accurate, and helpful. They're your greatest tool for onboarding new contributors and working effectively with AI tools.
