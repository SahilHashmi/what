from flask import Flask, Blueprint, request, jsonify, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os
from functools import wraps
import base64
import io

# Initialize Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
db = SQLAlchemy(app)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(50), nullable=False)  # 'ai_response', 'booking_fill', 'cancellation', 'peak_hours'
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    outlet = db.Column(db.String(100))
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'report_type': self.report_type,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'outlet': self.outlet,
            'created_at': self.created_at.isoformat(),
            'data': self.data
        }

class AnalyticsService:
    def __init__(self, app=None):
        self.app = app
        
    def get_ai_response_rate(self, start_date, end_date, outlet=None):
        """Calculate AI response success rate."""
        with self.app.app_context():
            # Simulate data retrieval
            total_queries = 1000
            ai_handled = 750
            human_handled = 250
            
            return {
                'total_queries': total_queries,
                'ai_handled': ai_handled,
                'human_handled': human_handled,
                'success_rate': (ai_handled / total_queries) * 100
            }

    def get_booking_fill_rate(self, start_date, end_date, outlet=None):
        """Calculate booking fill rate."""
        with self.app.app_context():
            # Simulate data retrieval
            total_slots = 500
            filled_slots = 420
            unfilled_slots = 80
            
            return {
                'total_slots': total_slots,
                'filled_slots': filled_slots,
                'unfilled_slots': unfilled_slots,
                'fill_rate': (filled_slots / total_slots) * 100
            }

    def get_cancellation_trends(self, start_date, end_date, outlet=None):
        """Get cancellation trends by outlet."""
        with self.app.app_context():
            # Simulate data retrieval
            total_bookings = 1000
            cancellations = 120
            cancellation_reasons = {
                'customer_no_show': 60,
                'double_booking': 30,
                'other': 30
            }
            
            return {
                'total_bookings': total_bookings,
                'cancellations': cancellations,
                'cancellation_rate': (cancellations / total_bookings) * 100,
                'reason_distribution': cancellation_reasons
            }

    def get_peak_hours(self, start_date, end_date, outlet=None):
        """Get peak hours for inquiries."""
        with self.app.app_context():
            # Simulate data retrieval
            peak_hours = {
                '09:00-10:00': 120,
                '10:00-11:00': 150,
                '11:00-12:00': 180,
                '12:00-13:00': 160,
                '13:00-14:00': 140,
                '14:00-15:00': 130,
                '15:00-16:00': 160,
                '16:00-17:00': 180,
                '17:00-18:00': 200
            }
            
            return {
                'peak_hours': peak_hours,
                'total_inquiries': sum(peak_hours.values()),
                'peak_hour': max(peak_hours, key=peak_hours.get)
            }

    def export_to_csv(self, data, filename):
        """Export data to CSV."""
        df = pd.DataFrame(data)
        csv_file = io.StringIO()
        df.to_csv(csv_file, index=False)
        csv_file.seek(0)
        return csv_file.getvalue()

    def export_to_excel(self, data, filename):
        """Export data to Excel."""
        df = pd.DataFrame(data)
        excel_file = io.BytesIO()
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        excel_file.seek(0)
        return excel_file.getvalue()

# Token management
tokens = set()

def generate_token():
    """Generate a secure token."""
    token = base64.b64encode(os.urandom(32)).decode('utf-8')
    tokens.add(token)
    return token

def verify_token(token):
    """Verify if token is valid."""
    return token in tokens

def token_required(f):
    """Decorator for token-based authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Auth-Token')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        if not verify_token(token):
            return jsonify({'error': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    return decorated

# API Routes
reports_bp = Blueprint('reports', __name__)
service = AnalyticsService(app)

token = generate_token()
print(f"Generated token: {token}")

@reports_bp.route('/token')
def get_token():
    """Get a new authentication token."""
    return jsonify({'token': token})

@reports_bp.route('/ai-response-rate', methods=['GET'])
@token_required
def get_ai_response_rate():
    """Get AI response success rate."""
    start_date = request.args.get('start_date', datetime.utcnow() - timedelta(days=30))
    end_date = request.args.get('end_date', datetime.utcnow())
    outlet = request.args.get('outlet')
    
    result = service.get_ai_response_rate(start_date, end_date, outlet)
    return jsonify(result)

@reports_bp.route('/booking-fill-rate', methods=['GET'])
@token_required
def get_booking_fill_rate():
    """Get booking fill rate."""
    start_date = request.args.get('start_date', datetime.utcnow() - timedelta(days=30))
    end_date = request.args.get('end_date', datetime.utcnow())
    outlet = request.args.get('outlet')
    
    result = service.get_booking_fill_rate(start_date, end_date, outlet)
    return jsonify(result)

@reports_bp.route('/cancellation-trends', methods=['GET'])
@token_required
def get_cancellation_trends():
    """Get cancellation trends."""
    start_date = request.args.get('start_date', datetime.utcnow() - timedelta(days=30))
    end_date = request.args.get('end_date', datetime.utcnow())
    outlet = request.args.get('outlet')
    
    result = service.get_cancellation_trends(start_date, end_date, outlet)
    return jsonify(result)

@reports_bp.route('/peak-hours', methods=['GET'])
@token_required
def get_peak_hours():
    """Get peak hours for inquiries."""
    start_date = request.args.get('start_date', datetime.utcnow() - timedelta(days=30))
    end_date = request.args.get('end_date', datetime.utcnow())
    outlet = request.args.get('outlet')
    
    result = service.get_peak_hours(start_date, end_date, outlet)
    return jsonify(result)

@reports_bp.route('/export', methods=['POST'])
@token_required
def export_data():
    """Export data to CSV or Excel."""
    data = request.json.get('data')
    report_type = request.json.get('report_type')
    format = request.json.get('format', 'csv')  # csv or excel
    
    if format == 'csv':
        csv_data = service.export_to_csv(data, f'{report_type}.csv')
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={report_type}.csv'}
        )
    elif format == 'excel':
        excel_data = service.export_to_excel(data, f'{report_type}.xlsx')
        return Response(
            excel_data,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename={report_type}.xlsx'}
        )
    else:
        return jsonify({'error': 'Invalid format. Supported formats: csv, excel'}), 400

# Register blueprint
app.register_blueprint(reports_bp, url_prefix='/reports')

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
