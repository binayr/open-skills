from datetime import datetime
from flask import Blueprint, abort, g
from db import db
from models import Employee, LeaveRequest, AuditLog
from notify import send_decision_email

bp = Blueprint("manager", __name__)


def _check_direct_report(req: LeaveRequest):
    emp = Employee.query.get(req.employee_id)
    if emp.manager_id != g.user.id:
        abort(403)
    return emp


@bp.post("/requests/<int:req_id>/approve")
def approve_request(req_id):
    req = LeaveRequest.query.get_or_404(req_id)
    if req.status != "PENDING":
        abort(409)
    emp = _check_direct_report(req)
    if emp.leave_balance_days - req.days < 0:
        abort(422, "insufficient balance")
    emp.leave_balance_days -= req.days
    req.status = "APPROVED"
    req.decided_by = g.user.id
    req.decided_at = datetime.utcnow()
    db.session.add(AuditLog(actor_id=g.user.id, action="APPROVE", target_id=req.id))
    db.session.commit()
    send_decision_email(emp, req)
    return {"ok": True}


@bp.post("/requests/<int:req_id>/reject")
def reject_request(req_id):
    req = LeaveRequest.query.get_or_404(req_id)
    if req.status != "PENDING":
        abort(409)
    emp = _check_direct_report(req)
    req.status = "REJECTED"
    req.decided_by = g.user.id
    req.decided_at = datetime.utcnow()
    db.session.add(AuditLog(actor_id=g.user.id, action="REJECT", target_id=req.id))
    db.session.commit()
    send_decision_email(emp, req)
    return {"ok": True}


@bp.get("/team/requests")
def team_requests():
    reports = Employee.query.filter_by(manager_id=g.user.id).all()
    ids = [e.id for e in reports]
    return {"requests": [r.id for r in LeaveRequest.query.filter(LeaveRequest.employee_id.in_(ids), LeaveRequest.status == "PENDING")]}
