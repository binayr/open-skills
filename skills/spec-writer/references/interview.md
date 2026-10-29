# Interview guide

Pick the questions that are still unanswered — don't run through the whole list. Ask at most 5 per
round, each with a suggested default ("I'll assume X unless you tell me otherwise"). Group them so the
person can answer in one message.

## Problem
- Who runs into this problem? (role, team, customer type) Roughly how many people?
- How often does it happen, and what does it cost today — time, money, complaints, risk?
- What do people do about it today? (workarounds are often the best spec input)
- Why now? Is there a deadline, a regulation, a customer commitment?

## Outcome
- If this works perfectly, what is different in 3 months? How would we measure it?
- What's the smallest version that would already help?
- Is this a request for a specific solution? If so — what problem is it solving? Would another
  solution be acceptable?

## Users and permissions
- Who uses the new behaviour? Who must *not* be able to use it?
- Does anyone need to approve, be notified, or be able to undo?

## Data and other systems
- What information does this need, and where does it come from today?
- Does it create or change information that other teams, reports or systems rely on?
- Any personal, financial, legal or safety-relevant data involved?

## Constraints
- What must not break or change?
- Any rules, policies, contracts or regulations that apply?
- Languages, countries, time zones, currencies, channels (email/SMS/app) involved?

## Edge cases — walk this list for every spec
Each item ends up as an acceptance criterion, an out-of-scope line, or an open question.
- **Missing or bad input** — field empty, wrong format, unknown value
- **Duplicates and repeats** — the same event twice, the user clicks twice, a retry
- **Changes and cancellations** — the thing changes or is cancelled midway
- **Timing** — late, early, overlapping, time zones, weekends/holidays, deadlines passing
- **Volume** — 1 item vs 10,000; what happens at peak
- **Permissions** — someone without rights tries; the responsible person is absent
- **Failure** — the other system is down, the email bounces, the payment fails; who finds out?
- **Silence** — if something is skipped or excluded automatically, who is told? (silent skips are a
  common source of incidents)
- **Undo** — can the action be reversed; what happens to things already sent or paid
- **History** — what happens to records created before the change
