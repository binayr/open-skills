from datetime import datetime
from flask import Blueprint, abort, g, request
from db import db
from models import Employee, LeaveRequest

bp = Blueprint("admin", __name__)


@bp.post("/admin/requests/bulk-approve")
def bulk_approve():
    """HR-admin tool added for the 2025 year-end backlog. Approves many requests at once."""
    if not g.user.is_hr_admin:
        abort(403)
    ids = request.json.get("request_ids", [])
    for req in LeaveRequest.query.filter(LeaveRequest.id.in_(ids)).all():
        emp = Employee.query.get(req.employee_id)
        emp.leave_balance_days -= req.days
        req.status = "APPROVED"
        req.decided_by = g.user.id
        req.decided_at = datetime.utcnow()
    db.session.commit()
    return {"approved": len(ids)}
