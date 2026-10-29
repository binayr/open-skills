---
name: spec-writer
description: Helps anyone — product owners, business analysts, operations leads, domain experts, as well as engineers — write an engineering-grade specification (spec, PRD, requirements doc, feature brief, change request, user story set) for a software change, then review that spec before build and check the finished build against it. Use this whenever someone wants to describe a new feature, change, fix, integration, report or automation so a team can build it — e.g. "write a spec", "turn this idea into requirements", "draft a PRD", "help me write this up for the dev team", "what should I give engineering", "review this spec", "is this ready to build", "did they build what we asked for" — even if they never say the word "spec".
metadata:
  author: Binay Kumar Ray
  version: "1.1"
  derived-from: write-spec (Agentic TMS)
---

# Spec writer

Help a person — often someone close to the business rather than an engineer — produce a spec that an
engineering team can build from without guessing, then check it before build and check the build
against it afterwards.

## What makes a spec good (and why it's worth the effort)

Most bad builds come from bad specs, and most bad specs fail in the same few ways:

1. **They describe a wish, not today.** If the spec doesn't say how things work now, the team will
   rebuild something that exists or break something nobody mentioned. → *Ground every statement about
   the current situation in a source.*
2. **They hide guesses.** An assumption written as a fact is the most expensive line in a spec.
   → *Label every statement: confirmed (with source), stated by the requester, or assumption.*
3. **They can't be tested.** "Should be fast and user-friendly" can't pass or fail. → *Acceptance
   criteria in Given / When / Then form, each one observable.*
4. **They bury decisions.** Open choices hidden in prose get decided silently by whoever writes the
   code. → *List decisions separately, each with a recommendation and who decides.*
5. **They have no edges.** No out-of-scope list, no edge cases, no plan for undoing it.

The skill exists to prevent those five failures. Everything below serves one of them.

Files in this skill (load when the step says so):
- [references/interview.md](references/interview.md) — question bank and edge-case checklist (steps 2, 4)
- [assets/spec-template.md](assets/spec-template.md) — the spec layout to copy (step 4)
- [references/example-spec.md](references/example-spec.md) — a filled-in Short spec (read once before writing)
- [references/evaluation.md](references/evaluation.md) — spec review and build check rubrics (steps 6, 7)
- `scripts/check_spec.py` — structural validator, Python 3 standard library only (step 5)

## Gotchas

- **No code available ≠ license to guess.** Without a repository or system docs, write technical
  unknowns as questions for engineering. Invented table names or APIs read as facts and get built on.
- **"The team says it's done" is not evidence.** In a build check it counts as 🗣 Stated → NOT CHECKED.
- **Solution-shaped requests hide the problem.** "Add a button that exports X" — ask what the export
  is for; the real need is often a report or a notification.
- **Length kills readership.** Business owners stop at page one. Keep TL;DR, open questions and
  decisions at the top; push bulky tables to an appendix.
- **Silent automation is a defect.** Anything skipped, excluded or failed automatically must tell a
  named person; check every spec for this.

## The three jobs

| The person says something like… | Job | Go to |
|---|---|---|
| "write a spec / requirements / PRD for…", "help me describe this for the devs" | **Write** | steps 1–5 |
| "review this spec", "is this ready to build?", "what's missing?" | **Evaluate the spec** | step 6 |
| "they built it — does it match?", "check the delivery against the spec" | **Check the build** | step 7 |

## How to talk to the person

Assume the person knows the business deeply and may not know engineering vocabulary. That's the
point: they bring the *what* and *why*; you bring the structure and the engineering questions.

- Plain language. If you must use a technical term, define it in a few words the first time.
- Ask few, good questions — at most 5 per round, each with a suggested default answer so they can
  just say "yes". Questions to choose from are in [references/interview.md](references/interview.md).
- If the person isn't available to answer, or asks for a first draft, don't stall: draft with clearly
  labelled assumptions and put the open questions at the top of the spec.
- Push back when it helps them. If the request is a solution ("add a button that…") ask for the
  problem behind it; if there's a simpler way (an existing feature, a config change, a manual step),
  say so and let them choose. Agreeing with a flawed request isn't kindness.

## Step 1 — Capture the request and size it

Write down the request in the person's own words (it goes in §1 of the spec). Your interpretation goes
elsewhere; keeping the two apart makes scope creep visible later.

Then pick a size and tell the person which one and why:

| Size | When | Output |
|---|---|---|
| **No spec** | a wording/typo change, a single setting, a fix whose cause and remedy are already proven | Say so. A short ticket is enough. |
| **Short** | one screen, report, rule or small fix; no new data stored, no other systems affected, no money/legal/safety impact, no business decision needed | Sections marked *[S]* in the template |
| **Full** | stores new data or changes existing data, touches another system or team, involves money/pricing/legal/safety/personal data, changes who can do what, or needs a business decision | Every section |

If any Full trigger applies, it's Full.

## Step 2 — Understand the problem (interview)

Use [references/interview.md](references/interview.md). Make sure you know, at minimum: who has the problem, how often and what
it costs today; what "solved" looks like (a measurable outcome, not a feature); who will use the
change; what must not break; deadlines or constraints.

## Step 3 — Find out how things work today (discovery)

This is the step that separates an engineering-grade spec from a wish list. Use whatever is
available, in this order, and record where each fact came from:

1. **What the person tells you** — label as *stated by <name/role>*.
2. **Documents and tools you can reach** — project docs, READMEs, wikis, tickets, previous specs,
   shared drives, connected tools (e.g. Confluence, Jira, Drive). Search for earlier work on the same
   topic; if something similar exists or was tried, the spec becomes "extend/fix X", not "build X".
3. **Project rules.** Look for files that state how the project must work (e.g. `CLAUDE.md`,
   `AGENTS.md`, `CONTRIBUTING.md`, `README`, architecture docs, "principles" or "invariants" pages).
   Note every rule your change could bump into and check the design against them.
4. **Code and data — only if available.** If a code repository is connected, read the relevant parts
   and cite them as `path/to/file:line`. Note which version/branch you read. Check how the project
   handles stored-data changes (e.g. migration files and how they're numbered) and whether other
   systems read or write the same data. If you can query data read-only, do; never change data while
   writing a spec.
   If no code is available, don't guess how the system works: write those points as **Questions for
   engineering** in §6 and move on. A good business spec with honest questions beats a confident one
   with invented internals.

Label every factual statement in the spec with one of:
- ✅ **Confirmed** — with its source (document, file:line, data query, named person)
- 🗣 **Stated** — by the requester or another named person, not independently checked
- ❓ **Assumption** — with who can confirm it

If you used a helper (subagent, search tool) for discovery, open at least the sources your design
depends on yourself before marking them Confirmed. Helpers sometimes report things that aren't there.

## Step 4 — Write the spec

Copy [assets/spec-template.md](assets/spec-template.md) and keep its order.
[references/example-spec.md](references/example-spec.md) shows a filled-in Short spec; read it once
if you haven't — it's the fastest way to see the expected level of detail.

Rules that matter most:
- **TL;DR first** (≤ 6 lines): the problem, the change, who's affected, decisions needed, size.
- **Gaps** numbered `G1, G2…` — each a specific difference between today and what's needed.
- **Decisions** numbered `D1…` — options, your recommendation first, consequence of each, who
  decides, and state: *Decided / Recommended (default unless someone objects) / Open – blocks <phase>*.
- **Acceptance criteria** numbered `AC1…` in **Given / When / Then**, each saying how it will be
  checked (demo, test, report, data check) and which gap it covers. Every gap needs at least one AC.
  An AC must be able to fail: "Then the customer receives an email within 15 minutes" — not "Then it
  works well".
- **Edge cases** — walk the checklist in [references/interview.md](references/interview.md) §Edge cases; each one is either an
  AC, an out-of-scope item, or an open question. Edge cases are where most build defects come from.
- **Success measures** (§9) are business outcomes measured after go-live ("calls about late
  deliveries drop 30% in 8 weeks"). They're different from ACs, which are checked before go-live.
- **Out of scope** — what this change deliberately doesn't do. It protects both the team and you.
- **Rollout and undo** — how it gets switched on (all at once, a pilot group, a flag), and how to turn
  it off if something goes wrong.
- Keep §6 (technical notes) factual and short. For a non-engineer author it may be mostly questions —
  that's fine and expected.
- **Keep it readable for the business owner.** They must be able to read the first page (TL;DR, open
  questions, decisions) in five minutes. Prefer tables to prose; a Short spec is usually 1–2 pages.
  If a Full spec grows past ~250 lines, move bulky detail (long edge-case tables, field lists) into an
  appendix at the end rather than cutting it.
- Include the label legend line from the template so readers know what ✅ / 🗣 / ❓ mean.
- Never put passwords, keys, or real personal data in a spec. Made-up examples are fine.

**Saving:** write a Markdown file. If the project has a specs/docs folder, follow its naming;
otherwise use `specs/<short-topic>-YYYY-MM-DD.md` in the folder the person is working in (ask if
unclear). Offer to convert to Word or a wiki page afterwards if they need it. On later revisions,
append to the Review log rather than silently rewriting decided sections.

## Step 5 — Self-check, then report

If you can run Python, run `python3 scripts/check_spec.py <spec.md>` and fix every ERROR, re-running
until it reports 0 errors. It checks structure (size chosen, required sections, every gap covered by
an AC, vague words in ACs, decision states, label legend, leftover placeholders) — not whether the
content is true. Then check by hand:
- [ ] Request captured verbatim; size stated with reason
- [ ] Every factual statement labelled ✅ / 🗣 / ❓ with a source or owner
- [ ] Every gap has ≥1 acceptance criterion; every AC is Given/When/Then and can fail
- [ ] Every decision has a recommendation, an owner, and a state
- [ ] Edge-case checklist walked
- [ ] Project rules found (or "none found") and checked
- [ ] Out of scope, rollout and undo present
- [ ] No jargon left undefined in the business sections

Then tell the person, briefly: the TL;DR, the decisions only they can make, and what is still an
assumption. Suggest the spec evaluation (step 6) before it goes to build.

## Step 6 — Evaluate the spec (before anyone builds)

The author's self-check isn't a review. Use [references/evaluation.md](references/evaluation.md) Part A.

- **Independence:** if you can start a fresh helper/subagent, give it only the spec file and the
  rubric (not your opinions) and ask for scores with evidence. Otherwise review it yourself, re-open
  the sources instead of trusting memory, and record the review as *self-review (not independent)*.
- **Check the reviewer:** confirm each failure it reports before acting on it; drop ones that don't
  hold and say so.
- **Verdict:** READY / READY WITH CHANGES / NOT READY, recorded in the spec's §14 with the date.
- **Approval belongs to people.** Build should start only after the business owner approves, and —
  when the author isn't an engineer — after an engineer has reviewed §6 and the ACs for feasibility.
  You never mark a spec approved on someone's behalf.
- Reviewing a spec that wasn't written with this skill: map its sections onto the template first,
  and treat missing structure (no numbered ACs, no labels) as "needs retrofit" rather than a failure
  of the idea. Offer to do the retrofit. (`scripts/check_spec.py` errors on such a spec are the
  retrofit list, not the verdict.)

## Step 7 — Check the build against the spec

Use [references/evaluation.md](references/evaluation.md) Part B. The heart of it is a table: every AC and gap → what was
delivered → evidence (demo seen, test result, screenshot, data check, `file:line` if code is
available) → PASS / FAIL / NOT CHECKED / CHANGED.

- Only count what was actually checked. "Engineering says it's done" is 🗣 Stated, not evidence; ask
  for the demo or the test result.
- Any difference between spec and build goes in §15 Deviations with the reason and who accepted it.
- Verdict always shows counts: e.g. *MATCHES SPEC — 8/10 ACs pass, 2 not checked (need live data),
  accepted by <owner>*. Values: MATCHES SPEC / MATCHES WITH CHANGES / DOES NOT MATCH.
- After go-live, the §9 success measures tell you whether the change solved the problem — schedule
  when to look.
