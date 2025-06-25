from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Worker(db.Model):
    __tablename__ = 'workers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    reliability_rating = db.Column(db.Float, default=0.0)
    total_shifts = db.Column(db.Integer, default=0)
    shifts_completed = db.Column(db.Integer, default=0)
    
    standby_records = db.relationship('StandbyRecord', backref='worker', lazy=True)
    
    def calculate_reliability(self):
        if self.total_shifts == 0:
            return 0.0
        return (self.shifts_completed / self.total_shifts) * 100

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'location': self.location,
            'reliability_rating': self.reliability_rating,
            'total_shifts': self.total_shifts,
            'shifts_completed': self.shifts_completed
        }

class StandbyRecord(db.Model):
    __tablename__ = 'standby_records'
    
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/confirmed/canceled
    ai_status = db.Column(db.String(20), default='pending')  # pending/confirmed
    shift_assigned = db.Column(db.Boolean, default=False)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'worker': self.worker.to_dict(),
            'date': self.date.strftime('%Y-%m-%d'),
            'status': self.status,
            'ai_status': self.ai_status,
            'shift_assigned': self.shift_assigned
        }

class Shift(db.Model):
    __tablename__ = 'shifts'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    role_required = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='open')  # open/filled/canceled
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'location': self.location,
            'role_required': self.role_required,
            'status': self.status
        }
