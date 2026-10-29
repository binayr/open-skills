# leave-app

Internal leave (holiday) request tool. Flask + SQLAlchemy.

## Rules (do not break)
1. Every approval or rejection MUST write an `AuditLog` row (who, what, when). Auditors check this yearly.
2. A manager may only act on leave requests of their **direct reports** (`Employee.manager_id`).
3. An employee's `leave_balance_days` must never go negative.
4. Employees are emailed on every decision about their request.

## Layout
- `models.py` — Employee, LeaveRequest, AuditLog
- `routes.py` — manager-facing endpoints
- `admin.py` — HR-admin tools
- `notify.py` — email helper
