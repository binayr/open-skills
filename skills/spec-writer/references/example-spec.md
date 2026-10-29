# Example — a filled-in Short spec

A fictional company. Shows the level of detail expected, the ✅/🗣/❓ labels, and how gaps, rules,
edge cases and acceptance criteria link up.

---

# Remind customers to book a delivery slot — spec

**Status:** Draft r1 · **Size:** Short — one automated email, uses data we already hold, no new system
**Owner (business):** Priya N., Customer Operations Lead · **Author:** Priya N. with Claude · **Date:** 2026-03-02
**Related:** ticket OPS-412; customer-complaints report Feb 2026

## Open questions to answer first
1. Can the email platform send from the "deliveries@" address? — who: IT — default: use "noreply@".

## 0. TL;DR
Customers who don't book a delivery slot within 2 days cause failed first deliveries. Send one reminder
email 48 h after the order is ready if no slot is booked. Affects customers and the support team.
Decision needed: D1 (reminder count). Size: Short.

## 1. Request (as stated)
> "Customers forget to pick a delivery slot and then the driver turns up and nobody's home. Can we
> nudge them automatically?" — Priya N., 2026-02-27

## 2. The problem and who has it
- **Who:** home-delivery customers; the support team who rebook failed deliveries.
- **Today:** ~18% of orders have no slot booked 48 h after "ready" 🗣 (Priya, from Feb report);
  each failed delivery costs a re-delivery fee of €22 ✅ (Finance rate card 2026, p.3).
- **Goal:** fewer orders reaching dispatch without a booked slot.

## 3. How it works today
- When an order is ready, the customer gets one "ready — book your slot" email ✅ (email template
  list in the help-centre admin, template "ORDER_READY").
- Nothing further is sent if they don't book ✅ (same admin; no other template references slots).
- Orders without a slot are dispatched on the default slot after 4 days 🗣 (Dispatch team lead, Tom R.).
- Whether the email platform can be triggered by "no slot after 48 h" ❓ — confirm with IT.

**Project rules that apply:** marketing-consent rules do *not* apply to service emails ✅ (Privacy
policy §4.2); all customer emails must include the order number ✅ (Brand guidelines, p.7).

## 4. Gaps
| # | Gap | Evidence |
|---|---|---|
| G1 | No reminder when a slot isn't booked | ✅ template list |
| G2 | Support can't see whether a reminder was sent | 🗣 Priya |

## 5. Proposed change
### 5.1 What changes for the user
48 h after the ORDER_READY email, if no slot is booked, the customer gets one reminder with a direct
"book your slot" link (fixes G1). The reminder appears in the order's history for support (fixes G2).
### 5.2 Business rules
- R1 Send at 48 h (±15 min) after ORDER_READY was sent, only if no slot is booked at that moment.
- R2 Send at most one reminder per order.
- R3 Don't send if the order is cancelled or already dispatched.
- R4 Email includes the order number and the booking link; language = customer's account language.
### 5.3 Edge cases
| Situation | What should happen | Covered by |
|---|---|---|
| Customer books at 47 h 59 min | No reminder | AC2 |
| Order cancelled before 48 h | No reminder | AC3 |
| Email bounces | Logged in order history; no retry | AC4 |
| Orders that were already "ready" on go-live day | Not reminded | Out of scope |

## 6. Technical notes and questions for engineering
- **Data:** a "reminder sent at" timestamp per order (new).
- **Other systems:** email platform; order history view used by support.
- **Questions for engineering:** Q1 can the email platform be triggered on a time condition, or does
  this need a scheduled job? Q2 where is the booking status stored?

## 7. Decisions
| # | Question | Options | Recommendation | Consequence | Who decides | State |
|---|---|---|---|---|---|---|
| D1 | One reminder or two? | 1 at 48 h / 2 at 48 h + 72 h | 1 — measure first | 2 may annoy; 1 may under-perform | Priya | Recommended |

## 8. Acceptance criteria
| # | Given | When | Then | Covers | How checked | Phase |
|---|---|---|---|---|---|---|
| AC1 | an order ready 48 h ago with no slot | the 48 h point passes | the customer receives one reminder email containing the order number and booking link within 15 min | G1 | test order in staging | 1 |
| AC2 | a slot booked before 48 h | the 48 h point passes | no reminder is sent | G1 | test order | 1 |
| AC3 | an order cancelled before 48 h | the 48 h point passes | no reminder is sent | G1 | test order | 1 |
| AC4 | a reminder was sent or bounced | support opens the order history | they see "slot reminder sent/bounced" with the time | G2 | demo to support | 1 |

## 9. Success measures
| Measure | Baseline | Target | When | Source |
|---|---|---|---|---|
| Orders without slot at 72 h | 18% | ≤ 10% | 6 weeks after go-live | weekly ops report |

## 10. Rollout and undo
Switch on for all customers on a Tuesday; support briefed the day before. Undo: switch off the
reminder; already-sent emails are not recalled.

## 11. Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Reminder sent after the customer booked by phone | Low | Low | R1 checks booking status at send time |

## 12. Out of scope
- SMS reminders (later, if email doesn't hit target).
- Reminders for orders already ready on go-live day.

## 13. Review log
- r1, 2026-03-02 — first draft (Priya N.)
