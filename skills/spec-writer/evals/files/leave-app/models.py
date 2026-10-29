from datetime import datetime
from db import db


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(200))
    manager_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=True)
    is_hr_admin = db.Column(db.Boolean, default=False)
    leave_balance_days = db.Column(db.Float, default=25.0)


class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    days = db.Column(db.Float)
    status = db.Column(db.String(20), default="PENDING")  # PENDING / APPROVED / REJECTED / CANCELLED
    decided_by = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer)
    action = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    at = db.Column(db.DateTime, default=datetime.utcnow)
