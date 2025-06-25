import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# --- Dynamic Path Setup for Separated Files ---
def find_ai_routes():
    """Find ai_routes.py in common locations"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Common locations to search
    search_paths = [
        os.path.join(current_dir, 'ai_settings'),  # Same parent folder
        os.path.join(os.path.dirname(current_dir), 'ai_settings'),  # Parent's ai_settings
        os.path.join(current_dir, '..', 'ai_settings'),  # Relative parent
        r"C:\Users\ashis\Watsapp\ai_settings",  # Absolute path
    ]
    
    for path in search_paths:
        ai_routes_file = os.path.join(path, 'ai_routes.py')
        if os.path.exists(ai_routes_file):
            return path
    
    return None

# Find and add ai_settings path
ai_path = find_ai_routes()
if ai_path:
    sys.path.append(ai_path)
    print(f"Found ai_routes at: {ai_path}")
else:
    print("Warning: ai_routes.py not found")

# --- Local Imports ---
from .models import db, Worker, StandbyRecord, Shift

# Try to import AI routes
try:
    import ai_routes
    ai_bp = ai_routes.ai_bp
    AI_AVAILABLE = True
    print("AI routes imported successfully")
except ImportError as e:
    print(f"Could not import AI routes: {e}")
    AI_AVAILABLE = False

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- Database Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///standby.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# --- Register Blueprints ---
if AI_AVAILABLE:
    app.register_blueprint(ai_bp)

# --- Create DB Tables ---
with app.app_context():
    db.create_all()

# --- Routes ---
@app.route('/api/workers', methods=['GET'])
def get_workers():
    workers = Worker.query.all()
    return jsonify([worker.to_dict() for worker in workers])

@app.route('/api/workers/<int:worker_id>', methods=['GET'])
def get_worker(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    return jsonify(worker.to_dict())

@app.route('/api/standby', methods=['GET'])
def get_standby_list():
    filter_by = request.args.get('filterBy', 'date')
    value = request.args.get('value')
    query = StandbyRecord.query.join(Worker)

    if filter_by == 'date' and value:
        date = datetime.strptime(value, '%Y-%m-%d')
        query = query.filter(StandbyRecord.date == date)
    elif filter_by == 'location' and value:
        query = query.filter(Worker.location == value)
    elif filter_by == 'role' and value:
        query = query.filter(Worker.role == value)

    records = query.all()
    return jsonify([record.to_dict() for record in records])

@app.route('/api/shifts', methods=['GET'])
def get_shifts():
    shifts = Shift.query.all()
    return jsonify([shift.to_dict() for shift in shifts])

@app.route('/api/assign-shift', methods=['POST'])
def assign_shift():
    data = request.json
    record_id = data.get('recordId')
    shift_id = data.get('shiftId')

    record = StandbyRecord.query.get_or_404(record_id)
    shift = Shift.query.get_or_404(shift_id)

    # Update reliability
    record.worker.total_shifts += 1
    record.worker.shifts_completed += 1
    record.worker.reliability_rating = record.worker.calculate_reliability()

    shift.status = 'filled'
    record.shift_assigned = True
    record.status = 'confirmed'
    record.ai_status = 'confirmed'
    record.shift_id = shift_id

    db.session.commit()

    return jsonify({
        'message': 'Shift assigned successfully',
        'record': record.to_dict(),
        'shift': shift.to_dict()
    })

@app.route('/api/notify-workers', methods=['POST'])
def notify_workers():
    data = request.json
    location = data.get('location')
    role = data.get('role')
    date = datetime.strptime(data.get('date'), '%Y-%m-%d')

    workers = Worker.query.filter_by(location=location, role=role).all()

    for worker in workers:
        standby_record = StandbyRecord(
            worker_id=worker.id,
            date=date,
            status='pending',
            ai_status='pending'
        )
        db.session.add(standby_record)

    db.session.commit()

    return jsonify({
        'message': 'Workers notified successfully',
        'workers_notified': len(workers)
    })

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)