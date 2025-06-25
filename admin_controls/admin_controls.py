from flask import Flask, Blueprint, request, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from datetime import datetime, timedelta
import os
from functools import wraps
import base64
import jwt

# Initialize Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///admin_controls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
db = SQLAlchemy(app)

# Role permissions
class Role:
    VIEW_ONLY = 'view_only'
    EDITOR = 'editor'
    SUPER_ADMIN = 'super_admin'
    
    PERMISSIONS = {
        VIEW_ONLY: ['read'],
        EDITOR: ['read', 'write'],
        SUPER_ADMIN: ['read', 'write', 'admin']
    }

# Models
class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

class IntegrationSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # 'zapier', 'google_sheets', etc.
    config = db.Column(db.JSON)
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'provider': self.provider,
            'config': self.config,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class WhatsAppToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_valid(self):
        return datetime.utcnow() < self.expires_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'token': self.token,
            'expires_at': self.expires_at.isoformat(),
            'created_at': self.created_at.isoformat()
        }

class DowntimeNotice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }

# Authentication
def generate_token(username, role):
    """Generate JWT token."""
    payload = {
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except:
        return None

def role_required(roles):
    """Decorator for role-based access control."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'Token is missing'}), 401
            
            payload = verify_token(token.replace('Bearer ', ''))
            if not payload:
                return jsonify({'error': 'Invalid token'}), 401
            
            if payload['role'] not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

# Admin Controls Service
class AdminControlsService:
    def __init__(self, app=None):
        self.app = app
        
    def create_integration_setting(self, name, provider, config, enabled=True):
        """Create a new integration setting."""
        with self.app.app_context():
            setting = IntegrationSetting(
                name=name,
                provider=provider,
                config=config,
                enabled=enabled
            )
            db.session.add(setting)
            db.session.commit()
            return setting.to_dict()

    def update_integration_setting(self, setting_id, data):
        """Update an existing integration setting."""
        with self.app.app_context():
            setting = IntegrationSetting.query.get_or_404(setting_id)
            setting.config = data.get('config', setting.config)
            setting.enabled = data.get('enabled', setting.enabled)
            db.session.commit()
            return setting.to_dict()

    def create_whatsapp_token(self, token, expires_at):
        """Create a new WhatsApp token."""
        with self.app.app_context():
            whatsapp_token = WhatsAppToken(
                token=token,
                expires_at=expires_at
            )
            db.session.add(whatsapp_token)
            db.session.commit()
            return whatsapp_token.to_dict()

    def create_downtime_notice(self, message, start_time, end_time, created_by):
        """Create a new downtime notice."""
        with self.app.app_context():
            notice = DowntimeNotice(
                message=message,
                start_time=start_time,
                end_time=end_time,
                created_by=created_by
            )
            db.session.add(notice)
            db.session.commit()
            return notice.to_dict()

# API Routes
admin_bp = Blueprint('admin', __name__)
service = AdminControlsService(app)

@admin_bp.route('/login', methods=['POST'])
def login():
    """Login and get JWT token."""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # In a real application, you would verify the password here
    user = AdminUser.query.filter_by(username=username).first()
    if user:
        token = generate_token(username, user.role)
        return jsonify({'token': token})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@admin_bp.route('/integrations', methods=['GET'])
@role_required([Role.VIEW_ONLY, Role.EDITOR, Role.SUPER_ADMIN])
def get_integration_settings():
    """Get all integration settings."""
    with current_app.app_context():
        settings = IntegrationSetting.query.all()
        return jsonify([s.to_dict() for s in settings])

@admin_bp.route('/integrations', methods=['POST'])
@role_required([Role.EDITOR, Role.SUPER_ADMIN])
def create_integration_setting():
    """Create a new integration setting."""
    data = request.json
    setting = service.create_integration_setting(
        data['name'],
        data['provider'],
        data['config'],
        data.get('enabled', True)
    )
    return jsonify(setting)

@admin_bp.route('/integrations/<int:setting_id>', methods=['PUT'])
@role_required([Role.EDITOR, Role.SUPER_ADMIN])
def update_integration_setting(setting_id):
    """Update an integration setting."""
    data = request.json
    setting = service.update_integration_setting(setting_id, data)
    return jsonify(setting)

@admin_bp.route('/whatsapp/tokens', methods=['GET'])
@role_required([Role.VIEW_ONLY, Role.EDITOR, Role.SUPER_ADMIN])
def get_whatsapp_tokens():
    """Get all WhatsApp tokens."""
    with current_app.app_context():
        tokens = WhatsAppToken.query.all()
        return jsonify([t.to_dict() for t in tokens])

@admin_bp.route('/whatsapp/tokens', methods=['POST'])
@role_required([Role.EDITOR, Role.SUPER_ADMIN])
def create_whatsapp_token():
    """Create a new WhatsApp token."""
    data = request.json
    token = service.create_whatsapp_token(
        data['token'],
        datetime.fromisoformat(data['expires_at'])
    )
    return jsonify(token)

@admin_bp.route('/downtime', methods=['GET'])
@role_required([Role.VIEW_ONLY, Role.EDITOR, Role.SUPER_ADMIN])
def get_downtime_notices():
    """Get all downtime notices."""
    with current_app.app_context():
        notices = DowntimeNotice.query.all()
        return jsonify([n.to_dict() for n in notices])

@admin_bp.route('/downtime', methods=['POST'])
@role_required([Role.EDITOR, Role.SUPER_ADMIN])
def create_downtime_notice():
    """Create a new downtime notice."""
    data = request.json
    notice = service.create_downtime_notice(
        data['message'],
        datetime.fromisoformat(data['start_time']),
        datetime.fromisoformat(data['end_time']),
        data['created_by']
    )
    return jsonify(notice)

# Register blueprint
app.register_blueprint(admin_bp, url_prefix='/admin')

# Create database tables
with app.app_context():
    db.create_all()

def create_test_user():
    """Create a test admin user."""
    with app.app_context():
        # Check if user already exists
        if AdminUser.query.filter_by(username='test_admin').first():
            print("Test admin user already exists")
            return
            
        # Create test admin user
        user = AdminUser(
            username='test_admin',
            password_hash='test_password_hash',  # In production, use proper password hashing
            role=Role.SUPER_ADMIN
        )
        db.session.add(user)
        db.session.commit()
        print("Created test admin user: test_admin")

if __name__ == '__main__':
    # Create test user
    create_test_user()
    
    # Run the application
    app.run(debug=True)
