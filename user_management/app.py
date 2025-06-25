from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(50), nullable=False)  # worker, client, admin
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    location = db.Column(db.String(100))
    preferred_roles = db.Column(db.PickleType)
    certifications = db.Column(db.PickleType)
    availability = db.Column(db.PickleType)
    start_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    add_to_whatsapp = db.Column(db.Boolean, default=False)
    add_to_standby_pool = db.Column(db.Boolean, default=False)
    send_welcome = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_type': self.user_type,
            'full_name': self.full_name,
            'phone': self.phone,
            'email': self.email,
            'location': self.location,
            'preferred_roles': self.preferred_roles,
            'certifications': self.certifications,
            'availability': self.availability,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'notes': self.notes,
            'add_to_whatsapp': self.add_to_whatsapp,
            'add_to_standby_pool': self.add_to_standby_pool,
            'send_welcome': self.send_welcome,
            'created_at': self.created_at.isoformat()
        }

@app.route('/users/add', methods=['POST'])
def add_user():
    data = request.json
    user = User(
        user_type=data.get('user_type'),
        full_name=data.get('full_name'),
        phone=data.get('phone'),
        email=data.get('email'),
        location=data.get('location'),
        preferred_roles=data.get('preferred_roles'),
        certifications=data.get('certifications'),
        availability=data.get('availability'),
        start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d') if data.get('start_date') else None,
        notes=data.get('notes'),
        add_to_whatsapp=data.get('add_to_whatsapp', False),
        add_to_standby_pool=data.get('add_to_standby_pool', False),
        send_welcome=data.get('send_welcome', False)
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User added successfully!', 'user': user.to_dict()}), 201

@app.route('/users/all', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@app.route('/users/update/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    user = User.query.get_or_404(user_id)
    for field in data:
        if hasattr(user, field):
            setattr(user, field, data[field])
    db.session.commit()
    return jsonify({'message': 'User updated successfully', 'user': user.to_dict()})

@app.route('/users/delete/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})

@app.route('/users/filter', methods=['GET'])
def filter_users():
    role = request.args.get('role')
    location = request.args.get('location')
    available_day = request.args.get('available')

    users = User.query.all()
    result = []
    for u in users:
        if role and (not u.preferred_roles or role not in u.preferred_roles):
            continue
        if location and u.location != location:
            continue
        if available_day and (not u.availability or available_day not in u.availability):
            continue
        result.append(u.to_dict())
    return jsonify(result)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
