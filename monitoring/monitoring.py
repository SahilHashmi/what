from flask import Flask, Blueprint, request, jsonify
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
import hashlib
import base64
import binascii

# Initialize Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///monitoring.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure key in production
db = SQLAlchemy(app)

# Generate a secure token
def generate_token():
    token = base64.b64encode(os.urandom(32)).decode('utf-8')
    return token

def verify_token(token):
    # In production, you would store tokens in a database and verify against it
    # For now, we'll just check if the token exists
    return bool(token)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Auth-Token')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        if not verify_token(token):
            return jsonify({'error': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    return decorated

# Models
class AutomationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    message_id = db.Column(db.String(100), nullable=False)
    handled_by = db.Column(db.String(20), nullable=False)  # 'ai' or 'human'
    confidence_score = db.Column(db.Float)
    response_time = db.Column(db.Float)  # in seconds
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'message_id': self.message_id,
            'handled_by': self.handled_by,
            'confidence_score': self.confidence_score,
            'response_time': self.response_time
        }

class MessageMatchRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    total_messages = db.Column(db.Integer, nullable=False)
    auto_resolved = db.Column(db.Integer, nullable=False)
    match_rate = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'total_messages': self.total_messages,
            'auto_resolved': self.auto_resolved,
            'match_rate': self.match_rate
        }

class FailedQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    message = db.Column(db.Text, nullable=False)
    intent = db.Column(db.String(100))  # What the AI thought the intent was
    actual_intent = db.Column(db.String(100))  # What it should have been
    confidence_score = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'message': self.message,
            'intent': self.intent,
            'actual_intent': self.actual_intent,
            'confidence_score': self.confidence_score
        }

class DailyConversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    total_conversations = db.Column(db.Integer, nullable=False)
    peak_hour = db.Column(db.Integer)  # 0-23
    average_response_time = db.Column(db.Float)  # in seconds
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'total_conversations': self.total_conversations,
            'peak_hour': self.peak_hour,
            'average_response_time': self.average_response_time
        }

# Service class
class MonitoringService:
    def __init__(self, app=None):
        self.app = app
        
    def log_message_handling(self, message_id, handled_by, confidence_score=None, response_time=None):
        with self.app.app_context():
            log = AutomationLog(
                message_id=message_id,
                handled_by=handled_by,
                confidence_score=confidence_score,
                response_time=response_time
            )
            db.session.add(log)
            db.session.commit()
            
            # Update daily match rate
            self._update_match_rate()

    def _update_match_rate(self):
        with self.app.app_context():
            today = datetime.utcnow().date()
            logs = AutomationLog.query.filter(
                AutomationLog.timestamp >= today
            ).all()
            
            total = len(logs)
            auto_resolved = len([l for l in logs if l.handled_by == 'ai'])
            
            if total > 0:
                match_rate = (auto_resolved / total) * 100
            else:
                match_rate = 0
                
            # Update or create daily match rate record
            record = MessageMatchRate.query.filter_by(date=today).first()
            if record:
                record.total_messages = total
                record.auto_resolved = auto_resolved
                record.match_rate = match_rate
            else:
                record = MessageMatchRate(
                    date=today,
                    total_messages=total,
                    auto_resolved=auto_resolved,
                    match_rate=match_rate
                )
                db.session.add(record)
            db.session.commit()

    def log_failed_query(self, message, intent, actual_intent, confidence_score):
        with self.app.app_context():
            query = FailedQuery(
                message=message,
                intent=intent,
                actual_intent=actual_intent,
                confidence_score=confidence_score
            )
            db.session.add(query)
            db.session.commit()

    def update_conversation_stats(self, date=None):
        if date is None:
            date = datetime.utcnow().date()
            
        with self.app.app_context():
            # Get logs for the day
            logs = AutomationLog.query.filter(
                AutomationLog.timestamp >= date,
                AutomationLog.timestamp < date + timedelta(days=1)
            ).all()
            
            # Calculate stats
            total_conversations = len(logs)
            
            # Get peak hour
            hour_counts = {}
            for log in logs:
                hour = log.timestamp.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None
            
            # Calculate average response time
            response_times = [log.response_time for log in logs if log.response_time is not None]
            average_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Update or create daily conversation record
            record = DailyConversation.query.filter_by(date=date).first()
            if record:
                record.total_conversations = total_conversations
                record.peak_hour = peak_hour
                record.average_response_time = average_response_time
            else:
                record = DailyConversation(
                    date=date,
                    total_conversations=total_conversations,
                    peak_hour=peak_hour,
                    average_response_time=average_response_time
                )
                db.session.add(record)
            db.session.commit()

# API Routes
monitoring_bp = Blueprint('monitoring', __name__)
service = MonitoringService(app)

token = generate_token()
print(f"Generated token: {token}")

@monitoring_bp.route('/token', methods=['GET'])
def get_token():
    return jsonify({'token': token})

@monitoring_bp.route('/data/automation-logs', methods=['GET'])
@token_required
def get_automation_logs():
    with app.app_context():
        logs = AutomationLog.query.order_by(AutomationLog.timestamp.desc()).all()
        return jsonify([log.to_dict() for log in logs])

@monitoring_bp.route('/data/match-rate', methods=['GET'])
@token_required
def get_match_rate():
    with app.app_context():
        date = request.args.get('date')
        if date:
            record = MessageMatchRate.query.filter_by(date=date).first()
            return jsonify(record.to_dict() if record else {})
        
        records = MessageMatchRate.query.order_by(MessageMatchRate.date.desc()).all()
        return jsonify([r.to_dict() for r in records])

@monitoring_bp.route('/data/failed-queries', methods=['GET'])
@token_required
def get_failed_queries():
    with app.app_context():
        queries = FailedQuery.query.order_by(FailedQuery.timestamp.desc()).all()
        return jsonify([q.to_dict() for q in queries])

@monitoring_bp.route('/data/conversation-stats', methods=['GET'])
@token_required
def get_conversation_stats():
    with app.app_context():
        date = request.args.get('date')
        if date:
            record = DailyConversation.query.filter_by(date=date).first()
            return jsonify(record.to_dict() if record else {})
        
        records = DailyConversation.query.order_by(DailyConversation.date.desc()).all()
        return jsonify([r.to_dict() for r in records])

# Register blueprint
app.register_blueprint(monitoring_bp, url_prefix='/monitoring')

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
