---
name: metis-idea-to-plan
description: Take a broad idea or goal and break it down into actionable phases, milestones, dependencies, and a rough timeline. Outputs a structured markdown plan; optionally writes it to Obsidian and/or queues milestones as background jobs.
---

# metis-idea-to-plan

Transform a vague intention ("I want to change careers", "I want to build an app")
into a concrete, actionable project plan. Metis listens to the user's goal,
identifies key phases, breaks each into 3-5 milestones, estimates effort, and
presents a structured plan the user can execute.

## Trigger Phrases

When you hear any of these from the user, activate this skill:

- "break this down"
- "help me plan"
- "what would it take to"
- "milestones for"
- "phases for"
- "how do I get started with"
- "roadmap for"
- "I want to..." (followed by a multi-step goal)
- "make a plan for"

Even if the user doesn't use these exact phrases, if they describe a complex,
multi-step goal that would benefit from decomposition, activate this skill
proactively.

## Environment

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OBSIDIAN_VAULT_PATH` | No | `~/Documents/Obsidian Vault` | Path to Obsidian vault for plan notes |
| `PLANS_DIR` | No | `Plans` | Subdirectory inside vault for plan documents |

## Workflow

### Step 1: Probe and Clarify

Before planning, understand the goal deeply. Ask targeted questions to scope the
effort:

- **Scope**: "What does success look like? What's the end state?"
- **Constraints**: "Any deadlines, budget limits, or resource constraints?"
- **Exclusions**: "What's explicitly out of scope for now?"
- **Existing context**: "Have you started anything on this already?"
- **Personal context**: "Is this for yourself, a team, or someone else?"

### Step 2: Check for Existing Plans

Search the user's Obsidian vault for any existing plans or notes related to this
goal. Use `search-notes` from the metis-obsidian skill with relevant keywords.
If a plan already exists, mention it and ask if they want to build on it or start
fresh.

Example prompt:

> I found an existing note at `Plans/Career Change.md` from last month. It
> explores some research on data science bootcamps. Do you want me to build on
> that, or start a fresh plan?

### Step 3: Identify Phases

Break the goal into 3-6 logical phases. Each phase should represent a coherent
chunk of work with a clear deliverable or outcome. Common phase patterns:

| Type | Example Phases |
|------|---------------|
| **Learning** | Foundation → Practice → Real Project → Portfolio → Application |
| **Product** | Research → Design → Prototype → Build → Launch → Iterate |
| **Career** | Self-Assessment → Skill Gap → Training → Networking → Transition |
| **Creative** | Ideation → Outline → Draft → Revision → Publication |
| **Health** | Assessment → Plan → Habits → Milestones → Maintenance |

Name each phase with a short, descriptive label and a one-liner outcome:

```
Phase 1: Foundation — "Be able to build and deploy a simple web app"
Phase 2: Core Stack — "Ship a full-stack CRUD application from scratch"
```

### Step 4: Break Phases into Milestones

For each phase, define 3-5 concrete milestones. Each milestone should be:

- **Verifiable**: you know when it's done (e.g., "Complete tutorial X" not "Learn Y")
- **Independent**: it can be done without waiting for other milestones in the same phase
- **Bite-sized**: achievable in a few days to a couple of weeks

For each milestone, estimate effort using this scale:

| Effort | Duration | Description |
|--------|----------|-------------|
| 🟢 **XS** | 1-2 hours | Single session task |
| 🔵 **S** | Half day | Focused session |
| 🟡 **M** | 1-3 days | Multi-session effort |
| 🟠 **L** | 1-2 weeks | Sustained effort |
| 🔴 **XL** | 2-4 weeks | Major milestone |

### Step 5: Map Dependencies

Identify cross-phase and cross-milestone dependencies:

- **Blocking**: "Can't start Phase 2 until Phase 1 is done"
- **Parallelizable**: "Phase 1 and Phase 2 research can happen simultaneously"
- **Optional**: "Nice-to-have but not blocking"

Present dependencies as a simple list under the plan header:

```
Dependencies:
- Phase 1 → Phase 2 (Blocking: must complete foundation before core stack)
- Phase 1.2 → Phase 2.1 (Blocking: must pick framework before building with it)
- Phase 3 + Phase 4 (Parallel: content creation and design can overlap)
```

### Step 6: Build the Rough Timeline

Derive a rough timeline from the effort estimates. Use weeks/months for long
plans, days for shorter ones. Mark this as an *estimate* — the user should
adjust based on their actual availability.

```
Rough Timeline (estimated at ~10 hrs/week):
- Phase 1: 2 weeks
- Phase 2: 3 weeks
- Phase 3: 4 weeks (runs parallel with Phase 4)
- Phase 4: 3 weeks
- Phase 5: 2 weeks
─────────────────────────
Total: ~14 weeks (3-4 months)
```

### Step 7: Present the Plan

Format the plan as clean markdown. Use this structure:

```markdown
# Plan: [Goal Title]

**Created:** [date]
**Status:** Draft

## Summary

One-paragraph overview of what this plan achieves.

## Dependencies

- [Phase A] → [Phase B] — description of dependency

## Phases

### Phase 1: [Name]
**Outcome:** [one-line outcome]
**Timeline:** [rough estimate]
**Status:** Not started

| # | Milestone | Effort | Notes |
|---|-----------|--------|-------|
| 1 | [Milestone name] | 🟡 M | [brief note] |
| 2 | [Milestone name] | 🔵 S | [brief note] |
| 3 | [Milestone name] | 🟠 L | [brief note] |

### Phase 2: [Name]
...

## Rough Timeline

| Phase | Estimate |
|-------|----------|
| Phase 1 | X weeks |
| ... | ... |
| **Total** | **X weeks** |

## Next Steps

- [ ] Review and adjust the plan
- [ ] (Optional) Queue milestones as background tasks
- [ ] (Optional) Save this plan to Obsidian
```

### Step 8: Offer to Save to Obsidian

After presenting the plan, ask:

> **Would you like me to:**
> 1. Save this plan to Obsidian (`Plans/[Title].md`)
> 2. Keep it in our conversation for now
> 3. Both

If the user chooses option 1 or 3, use the `metis-obsidian` skill's create-note
workflow to write the plan to `$OBSIDIAN_VAULT_PATH/$PLANS_DIR/<Title>.md`,
then run git-sync.

### Step 9: Offer to Queue Milestones

For complex, long-term plans, ask:

> **This plan has [N] milestones across [M] phases. Do you want me to queue**
> **individual milestones as background tasks? I can start working through**
> **them in order while you focus on other things.**

If the user says yes:

1. Label each milestone as a separate job with a descriptive title
2. Start with Phase 1 milestones in dependency order
3. Set appropriate effort estimates as job parameters
4. Track job progress and report back on completion

### Step 10: Cross-Reference Later

If the user returns to a topic that has an existing plan:

1. Search the vault for `$PLANS_DIR/*.md` matching relevant keywords
2. Mention the existing plan and its status
3. Ask if they want to update the plan, start executing, or create a new one

Use `search-notes` from metis-obsidian to find matching plans.

## Complete Example

**User:** "I want to change careers into tech. Help me plan that."

**Metis:**

> Great goal! Let me ask a few questions to scope this:
>
> 1. **What area of tech?** (Software engineering, data science, product, design, etc.)
> 2. **Timeline?** Any deadline you're working toward?
> 3. **Current situation?** Any existing skills or experience?
> 4. **Budget?** Thinking of bootcamps, self-study, or degrees?

*[User responds: "Software engineering, self-study, 12 months, some Python basics"]*

> Let me check if you already have notes on this...
>
> *(searches vault)*
>
> I see you have `Plans/Learn to Code.md` from a few months ago with some
> initial research. Want me to incorporate that or start fresh?
>
> *[User: "Build on it"]*
>
> Great. Here's a structured plan:

---

> # Plan: Career Change — Software Engineering
>
> **Created:** 2026-04-26
> **Status:** Draft
> **Based on:** [[Plans/Learn to Code]]
>
> ## Summary
>
> Transition from current career to software engineering over ~12 months through
> self-study, project building, and portfolio development. Starting from Python
> basics, ending with a job-ready portfolio and active job search.
>
> ## Dependencies
>
> - Phase 1 → Phase 2 → Phase 3 (Sequential — each builds on the last)
> - Phase 4 runs in parallel with Phase 3 (start portfolio while building projects)
> - Phase 5 → Phase 6 (Application phase depends on portfolio readiness)
>
> ## Phases
>
> ### Phase 1: Foundation (6 weeks)
> **Outcome:** Comfortable with Python, Git, and basic CS concepts
> **Timeline:** 6 weeks
>
> | # | Milestone | Effort | Notes |
> |---|-----------|--------|-------|
> | 1 | Complete Python for Everybody (Coursera) | 🟠 L | Existing Python basics will accelerate this |
> | 2 | Git & GitHub fundamentals | 🟡 M | Version control is a must before any project |
> | 3 | CS50x weeks 0-4 | 🔴 XL | Core CS concepts — take it slow |
> | 4 | Build a CLI todo app | 🟡 M | First real project, keep it simple |
>
> ### Phase 2: Web Development Core (8 weeks)
> **Outcome:** Can build and deploy a basic web app
> **Timeline:** 8 weeks
>
> | # | Milestone | Effort | Notes |
> |---|-----------|--------|-------|
> | 1 | HTML/CSS/JS fundamentals | 🟡 M | Enough to be dangerous, not a designer |
> | 2 | Pick a framework (React or Django) | 🔵 S | Evaluate both, commit to one |
> | 3 | Build a CRUD web app with auth | 🔴 XL | The milestone that proves capability |
> | 4 | Deploy to a free platform | 🟡 M | Render, Railway, or Vercel |
>
> ... (remaining phases)
>
> ## Rough Timeline
>
> | Phase | Estimate |
> |-------|----------|
> | Phase 1: Foundation | 6 weeks |
> | Phase 2: Web Dev Core | 8 weeks |
> | Phase 3: Deep Dive | 10 weeks |
> | Phase 4: Portfolio (parallel) | 6 weeks |
> | Phase 5: Job Prep | 6 weeks |
> | Phase 6: Application | 8 weeks |
> | **Total** | **~12 months** |
>
> ## Next Steps
>
> - [ ] Review and adjust the plan
> - [ ] Adjust timeline based on actual weekly hours
> - [ ] Would you like me to save this to Obsidian?
> - [ ] Or start queuing Phase 1 milestones as background tasks?

## Pitfalls

- **Don't over-plan.** For simpler goals (1-3 steps), just outline the steps
  inline instead of building a full phase/milestone structure. The user doesn't
  need a 5-phase plan for "clean up my desktop."
- **Don't assume availability.** Always ask about time commitment before giving
  a timeline. "10 hrs/week" yields a very different timeline than "2 hrs/week."
- **Don't skip the probe step.** A plan for a vague goal is useless. Two
  clarifying questions up front save three revisions later.
- **Don't forget existing context.** The user may have notes, research, or prior
  plans. Always check before building from scratch.
- **Don't present a wall of text.** Format the plan with clear headings, tables,
  and whitespace. Use emoji sparingly for effort indicators.
- **Don't queue without consent.** Even for large plans, ask before using
  background tasks. The user may want to review the plan first.
- **Don't overestimate dependencies.** Many milestones in different phases can
  run in parallel. Default to "parallel" unless there's a clear blocking
  relationship.
- **Plan scope creep.** If the user starts adding goals mid-conversation,
  suggest a separate plan rather than bloating the current one.
