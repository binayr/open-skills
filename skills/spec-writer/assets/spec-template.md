# Spec template

Copy this structure. Sections marked **[S]** are required for Short specs; Full specs use every
section. Write "None" rather than deleting a required section — "None" is an answer, a missing
section is a question.

Labels for factual statements: ✅ Confirmed (source) · 🗣 Stated (by whom) · ❓ Assumption (who confirms)

---

```markdown
# <Short, plain title> — spec

**Status:** Draft r1 | Reviewed r1 (<verdict>) | Approved r1 | Built | Done
**Size:** Short | Full — <one-line reason>
**Owner (business):** <name, role> · **Author:** <name> · **Date:** YYYY-MM-DD
**Related:** <tickets, earlier specs, documents>
**Labels used below:** ✅ Confirmed (with source) · 🗣 Stated (by whom, not checked) · ❓ Assumption (who can confirm)

## Open questions to answer first            <!-- only while any are open; remove when empty -->
1. <question> — who can answer: <role> — default if no answer: <…>

## 0. TL;DR [S]
<≤6 lines: problem · change · who is affected · decisions needed · size>

## 1. Request (as stated) [S]
> <the request in the requester's own words, with who and when>

## 2. The problem and who has it [S]
- **Who:** <users/roles/customers affected>
- **Today:** <what happens now, how often, what it costs — each line labelled ✅/🗣/❓>
- **Goal:** <what "solved" looks like, in outcome terms>

## 3. How it works today [S]
<the current process/system behaviour relevant to this change — every statement labelled with a source.
If code was available, cite `path/file:line` and the version/branch read.>

**Project rules that apply:** <rule — source>  · or "None found (searched: …)"

## 4. Gaps [S]
| # | What's missing or wrong today | Evidence |
|---|---|---|
| G1 | | ✅/🗣/❓ + source |

## 5. Proposed change [S]
### 5.1 What changes for the user
<plain-language walk-through of the new behaviour, step by step — "fixes G1">
### 5.2 Business rules
<numbered rules: R1 …; each exact enough that two engineers would build the same thing>
### 5.3 Edge cases
| Situation | What should happen | Covered by |
|---|---|---|
| | | AC# / Out of scope / Open question |

## 6. Technical notes and questions for engineering [S: may be mostly questions]
- **Data:** <new or changed information stored; where it comes from>
- **Other systems / teams affected:** <…>
- **Permissions:** <who can see / do what>
- **Questions for engineering:** <numbered; each with why it matters>

## 7. Decisions [S: one line, "None" allowed]
| # | Question | Options | Recommendation | Consequence | Who decides | State |
|---|---|---|---|---|---|---|
| D1 | | | | | | Decided / Recommended / Open – blocks <phase> |

## 8. Acceptance criteria [S]
| # | Given | When | Then | Covers | How checked | Phase |
|---|---|---|---|---|---|---|
| AC1 | | | | G1 | demo / test / report / data check | 1 |

## 9. Success measures (after go-live)
| Measure | Today (baseline) | Target | When to check | Source |
|---|---|---|---|---|

## 10. Rollout and undo [S: one line]
<how it's switched on (pilot group / all / behind a switch) · who's told · how to turn it off · what
happens to data created meanwhile>

## 11. Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|

## 12. Out of scope [S]
- <deliberately not included, and why>

## 13. Review log [S]
- r1, YYYY-MM-DD — first draft (<author>)

## 14. Spec review                              <!-- added at review, before build -->
**Date · reviewer (independent / self-review) · revision reviewed**
<scores from evaluation.md Part A · issues found · issues dropped after checking>
**Verdict:** READY | READY WITH CHANGES | NOT READY
**Approved by (business):** <name, date> · **Engineering review:** <name, date>

## 15. Build check                              <!-- added after build -->
### 15.1 Deviations
| What changed vs spec | Why | Affects | Accepted by |
|---|---|---|---|
### 15.2 Acceptance results
| AC | Delivered as | Evidence | Result |
|---|---|---|---|
**Verdict:** MATCHES SPEC | MATCHES WITH CHANGES | DOES NOT MATCH — <n/m ACs pass, k not checked>
### 15.3 Not yet checked / follow-ups
```
