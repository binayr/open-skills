# Evaluation rubrics

Score each item **PASS / WEAK / FAIL / N/A** with one line of evidence (quote the spec, cite the
source). ★ items apply to every spec; the rest apply to Full specs (N/A for Short unless relevant).

## Part A — Spec review (before build)

Brief for an independent reviewer (subagent or colleague):
> Review the spec at `<path>` against Part A of `references/evaluation.md` in the spec-writer skill.
> Re-open the sources the spec cites where you can; don't take its claims on trust. Return: item ·
> score · evidence, then the list of blocking issues, then a verdict. Don't edit the spec.

If the spec wasn't written with this skill, first map its sections to the template; missing structure
(no numbered ACs, no labels) scores WEAK – "needs retrofit", not FAIL.

| # | Item | What to check |
|---|---|---|
| A1 ★ | Request captured | §1 holds the request as stated, separate from interpretation. |
| A2 ★ | Today is grounded | Statements about the current situation are labelled ✅/🗣/❓ with sources. Spot-check ≥3 ✅ items (all of them if few). Unlabelled facts or a wrong ✅ = FAIL. |
| A3 ★ | Not already solved | Evidence that existing features, earlier specs or workarounds were looked for. |
| A4 ★ | Gaps → ACs | Every gap has ≥1 AC; every AC traces to a gap. |
| A5 ★ | ACs can fail | Each AC is Given/When/Then, observable, with a "how checked". Vague words ("fast", "easy", "appropriate", "etc.") = FAIL. |
| A6 ★ | Rules are unambiguous | Two engineers reading §5.2 would build the same thing. Numbers, limits, time frames stated. |
| A7 ★ | Edge cases walked | Interview edge-case list covered; each case resolved to AC / out of scope / open question. |
| A8 ★ | Decisions surfaced | Every choice the build depends on is in §7 with a recommendation, an owner and a state; none blocking phase 1 is Open. |
| A9 ★ | Scope fenced | Out-of-scope list present; design doesn't silently exceed the request. |
| A10 ★ | Rollout and undo | How it is switched on and how it is turned off are stated. |
| A11 | Project rules respected | Applicable rules listed with source, and the design checked against them. |
| A12 | Other systems and data | Data created/changed and other affected systems/teams named; questions for engineering where unknown. |
| A13 | Success measurable | §9 has a baseline, a target and a date. |
| A14 | Simpler option considered | Would an existing feature, setting or manual step solve most of it? If so, is the choice justified? |
| A15 | Readable by both sides | Business sections jargon-free; technical sections precise. |

**Verdict:** any FAIL → **NOT READY**. Only WEAK → **READY WITH CHANGES**. All PASS/N/A → **READY**.
Record in §14. Approval is given by people (business owner, plus engineering review when the author
isn't an engineer) — the reviewer only recommends.

## Part B — Build check (after build, per phase)

Brief for an independent checker:
> Check the delivered change against the spec at `<path>` using Part B of `references/evaluation.md`.
> Use only evidence you can see (demo notes, test results, screenshots, data checks, code if
> available). Return the acceptance table, item scores, and a verdict with counts. Don't edit anything.

### Acceptance table (required)

| AC / Gap | Delivered as | Evidence | Result |
|---|---|---|---|
| AC1 | | demo 2026-xx-xx / test name / screenshot / `file:line` | PASS / FAIL / NOT CHECKED / CHANGED |

| # | Item | What to check |
|---|---|---|
| B1 ★ | Every AC has evidence | PASS needs something seen, not "the team says so" (that's 🗣, counts as NOT CHECKED). |
| B2 ★ | Nothing missing | Every gap for this phase is closed or explicitly deferred. |
| B3 ★ | No silent changes | Every difference from the spec is in §15.1 with a reason and who accepted it. |
| B4 ★ | Edge cases tried | The edge-case table was exercised, at least the ones marked as ACs. |
| B5 | Nothing extra | Unplanned changes are explained (extra features carry extra risk). |
| B6 | Rollout ready | The switch-on and undo described in §10 exist and were tried. |
| B7 | Success tracking ready | The §9 measures can actually be collected after go-live. |

**Verdict** (always with counts, e.g. "8/10 ACs pass, 2 not checked"): any FAIL → **DOES NOT
MATCH**. Differences documented and accepted → **MATCHES WITH CHANGES** (update the spec). Else
**MATCHES SPEC**. NOT CHECKED items need the business owner's explicit acceptance.
