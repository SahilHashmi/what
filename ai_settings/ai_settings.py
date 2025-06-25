from flask import Flask, Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
import os
import operator

# Initialize Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ai_settings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# AI Models
class AITemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_type': self.template_type,
            'subject': self.subject,
            'content': self.content
        }

class TrainingData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'response': self.response,
            'category': self.category
        }

class FallbackRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    condition = db.Column(db.String(200), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'condition': self.condition,
            'action': self.action,
            'priority': self.priority,
            'enabled': self.enabled
        }

class OfficeHours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    timezone = db.Column(db.String(50), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'timezone': self.timezone
        }

# AI Service class
class AIService:
    def _init_(self, app=None):
        self.app = app
        self.templates = {
            'confirmation': None,
            'cancellation': None,
            'inquiry': None
        }
        self.training_data = []
        self.fallback_rules = []
        self.office_hours = []
        
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.load_data()

    def load_data(self):
        with self.app.app_context():
            self.load_templates()
            self.load_training_data()
            self.load_fallback_rules()
            self.load_office_hours()

    def load_templates(self):
        with self.app.app_context():
            templates = AITemplate.query.all()
            for template in templates:
                self.templates[template.template_type] = template

    def load_training_data(self):
        with self.app.app_context():
            self.training_data = TrainingData.query.all()

    def load_fallback_rules(self):
        with self.app.app_context():
            self.fallback_rules = FallbackRule.query.order_by(FallbackRule.priority).all()

    def load_office_hours(self):
        with self.app.app_context():
            self.office_hours = OfficeHours.query.all()

    def get_template(self, template_type):
        return self.templates.get(template_type)

    def get_training_response(self, question):
        for data in self.training_data:
            if question.lower() in data.question.lower():
                return data.response
        return None

    def evaluate_condition(self, condition, confidence_score):
        """Safely evaluate fallback conditions without using eval()"""
        try:
            # Simple condition parser for basic operations
            condition = condition.replace('confidence_score', str(confidence_score))
            
            # Parse simple conditions like "< 0.5", "> 0.8", etc.
            operators = {
                '<': operator.lt,
                '<=': operator.le,
                '>': operator.gt,
                '>=': operator.ge,
                '==': operator.eq,
                '!=': operator.ne
            }
            
            for op_str, op_func in operators.items():
                if op_str in condition:
                    parts = condition.split(op_str)
                    if len(parts) == 2:
                        left = float(parts[0].strip())
                        right = float(parts[1].strip())
                        return op_func(left, right)
            
            return False
        except:
            return False

    def should_fallback(self, confidence_score):
        for rule in self.fallback_rules:
            if rule.enabled and self.evaluate_condition(rule.condition, confidence_score):
                return rule.action
        return None

    def is_within_office_hours(self):
        now = datetime.utcnow()
        current_time = now.time()
        current_day = now.weekday()
        
        for hours in self.office_hours:
            if hours.day_of_week == current_day:
                if hours.start_time <= current_time <= hours.end_time:
                    return True
        return False

    def get_escalation_flow(self):
        flow = []
        for rule in self.fallback_rules:
            if rule.enabled:
                flow.append({
                    'condition': rule.condition,
                    'action': rule.action,
                    'priority': rule.priority
                })
        return sorted(flow, key=lambda x: x['priority'])

    def create_template(self, template_type, subject, content):
        template = AITemplate(
            template_type=template_type,
            subject=subject,
            content=content
        )
        db.session.add(template)
        db.session.commit()
        self.templates[template_type] = template
        return template

    def create_training_data(self, question, response, category):
        training = TrainingData(
            question=question,
            response=response,
            category=category
        )
        db.session.add(training)
        db.session.commit()
        self.training_data.append(training)
        return training

    def create_fallback_rule(self, condition, action, priority, enabled=True):
        rule = FallbackRule(
            condition=condition,
            action=action,
            priority=priority,
            enabled=enabled
        )
        db.session.add(rule)
        db.session.commit()
        self.load_fallback_rules()  # Reload to maintain order
        return rule

    def create_office_hours(self, day_of_week, start_time, end_time, timezone):
        hours = OfficeHours(
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone
        )
        db.session.add(hours)
        db.session.commit()
        self.office_hours.append(hours)
        return hours

    def update_template(self, template_id, **kwargs):
        template = db.session.get(AITemplate, template_id)  # Updated method
        if template:
            for key, value in kwargs.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            db.session.commit()
            self.load_templates()  # Reload templates
            return template
        return None

    def delete_template(self, template_id):
        template = db.session.get(AITemplate, template_id)  # Updated method
        if template:
            db.session.delete(template)
            db.session.commit()
            self.load_templates()  # Reload templates
            return True
        return False

    def update_training_data(self, training_id, **kwargs):
        training = db.session.get(TrainingData, training_id)  # Updated method
        if training:
            for key, value in kwargs.items():
                if hasattr(training, key):
                    setattr(training, key, value)
            db.session.commit()
            self.load_training_data()  # Reload data
            return training
        return None

    def delete_training_data(self, training_id):
        training = db.session.get(TrainingData, training_id)  # Updated method
        if training:
            db.session.delete(training)
            db.session.commit()
            self.load_training_data()  # Reload data
            return True
        return False

    def update_fallback_rule(self, rule_id, **kwargs):
        rule = db.session.get(FallbackRule, rule_id)  # Updated method
        if rule:
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            db.session.commit()
            self.load_fallback_rules()  # Reload rules
            return rule
        return None

    def delete_fallback_rule(self, rule_id):
        rule = db.session.get(FallbackRule, rule_id)  # Updated method
        if rule:
            db.session.delete(rule)
            db.session.commit()
            self.load_fallback_rules()  # Reload rules
            return True
        return False

    def update_office_hours(self, hours_id, **kwargs):
        hours = db.session.get(OfficeHours, hours_id)  # Updated method
        if hours:
            for key, value in kwargs.items():
                if hasattr(hours, key):
                    if key in ['start_time', 'end_time'] and isinstance(value, str):
                        value = datetime.strptime(value, '%H:%M').time()
                    setattr(hours, key, value)
            db.session.commit()
            self.load_office_hours()  # Reload hours
            return hours
        return None

    def delete_office_hours(self, hours_id):
        hours = db.session.get(OfficeHours, hours_id)  # Updated method
        if hours:
            db.session.delete(hours)
            db.session.commit()
            self.load_office_hours()  # Reload hours
            return True
        return False

# Initialize AIService
service = AIService()

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')
# API Routes - Templates

@ai_bp.route('/status', methods=['GET'])
def status():
    return jsonify({'message': 'AI route active'})
@app.route('/ai/templates', methods=['GET'])
def get_templates():
    templates = AITemplate.query.all()
    return jsonify([t.to_dict() for t in templates])

@app.route('/ai/templates', methods=['POST'])
def create_template():
    try:
        data = request.json
        if not data or not all(k in data for k in ['template_type', 'subject', 'content']):
            return jsonify({'error': 'Missing required fields: template_type, subject, content'}), 400
        
        template = service.create_template(
            template_type=data['template_type'],
            subject=data['subject'],
            content=data['content']
        )
        return jsonify(template.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai/templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    try:
        data = request.json
        template = service.update_template(template_id, **data)
        if template:
            return jsonify(template.to_dict())
        return jsonify({'error': 'Template not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    try:
        if service.delete_template(template_id):
            return jsonify({'message': 'Template deleted successfully'})
        return jsonify({'error': 'Template not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Routes - Training Data
@app.route('/ai/training', methods=['GET'])
def get_training_data():
    training = TrainingData.query.all()
    return jsonify([t.to_dict() for t in training])

@app.route('/ai/training', methods=['POST'])
def create_training_data():
    try:
        data = request.json
        if not data or not all(k in data for k in ['question', 'response', 'category']):
            return jsonify({'error': 'Missing required fields: question, response, category'}), 400
        
        training = service.create_training_data(
            question=data['question'],
            response=data['response'],
            category=data['category']
        )
        return jsonify(training.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai/training/<int:training_id>', methods=['PUT'])
def update_training_data(training_id):
    try:
        data = request.json
        training = service.update_training_data(training_id, **data)
        if training:
            return jsonify(training.to_dict())
        return jsonify({'error': 'Training data not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai/training/<int:training_id>', methods=['DELETE'])
def delete_training_data(training_id):
    try:
        if service.delete_training_data(training_id):
            return jsonify({'message': 'Training data deleted successfully'})
        return jsonify({'error': 'Training data not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Routes - Fallback Rules
@app.route('/ai/fallback', methods=['GET'])
def get_fallback_rules():
    rules = FallbackRule.query.order_by(FallbackRule.priority).all()
    return jsonify([r.to_dict() for r in rules])

@app.route('/ai/fallback', methods=['POST'])
def create_fallback_rule():
    try:
        data = request.json
        if not data or not all(k in data for k in ['condition', 'action', 'priority']):
            return jsonify({'error': 'Missing required fields: condition, action, priority'}), 400
        
        rule = service.create_fallback_rule(
            condition=data['condition'],
            action=data['action'],
            priority=data['priority'],
            enabled=data.get('enabled', True)
        )
        return jsonify(rule.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai/fallback/<int:rule_id>', methods=['PUT'])
def update_fallback_rule(rule_id):
    try:
        data = request.json
        rule = service.update_fallback_rule(rule_id, **data)
        if rule:
            return jsonify(rule.to_dict())
        return jsonify({'error': 'Rule not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai/fallback/<int:rule_id>', methods=['DELETE'])
def delete_fallback_rule(rule_id):
    try:
        if service.delete_fallback_rule(rule_id):
            return jsonify({'message': 'Rule deleted successfully'})
        return jsonify({'error': 'Rule not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Routes - Office Hours
@app.route('/ai/office-hours', methods=['GET'])
def get_office_hours():
    hours = OfficeHours.query.all()
    return jsonify([h.to_dict() for h in hours])

@app.route('/ai/office-hours', methods=['POST'])
def create_office_hours():
    try:
        data = request.json
        if not data or not all(k in data for k in ['day_of_week', 'start_time', 'end_time', 'timezone']):
            return jsonify({'error': 'Missing required fields: day_of_week, start_time, end_time, timezone'}), 400
        
        hours = service.create_office_hours(
            day_of_week=data['day_of_week'],
            start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
            end_time=datetime.strptime(data['end_time'], '%H:%M').time(),
            timezone=data['timezone']
        )
        return jsonify(hours.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai/office-hours/<int:hours_id>', methods=['PUT'])
def update_office_hours(hours_id):
    try:
        data = request.json
        hours = service.update_office_hours(hours_id, **data)
        if hours:
            return jsonify(hours.to_dict())
        return jsonify({'error': 'Office hours not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai/office-hours/<int:hours_id>', methods=['DELETE'])
def delete_office_hours(hours_id):
    try:
        if service.delete_office_hours(hours_id):
            return jsonify({'message': 'Office hours deleted successfully'})
        return jsonify({'error': 'Office hours not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Additional utility endpoints
@app.route('/ai/status', methods=['GET'])
def get_ai_status():
    try:
        return jsonify({
            'status': 'active',
            'templates_count': AITemplate.query.count(),
            'training_data_count': TrainingData.query.count(),
            'fallback_rules_count': FallbackRule.query.count(),
            'office_hours_count': OfficeHours.query.count(),
            'within_office_hours': service.is_within_office_hours(),
            'escalation_flow': service.get_escalation_flow()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai/query', methods=['POST'])
def process_query():
    try:
        data = request.json
        if not data or 'question' not in data:
            return jsonify({'error': 'Missing required field: question'}), 400
        
        question = data['question']
        confidence_score = data.get('confidence_score', 0.8)
        
        # Try to get response from training data
        response = service.get_training_response(question)
        if response:
            return jsonify({
                'response': response,
                'source': 'training_data',
                'confidence_score': confidence_score
            })
        
        # Check if fallback is needed
        fallback_action = service.should_fallback(confidence_score)
        if fallback_action:
            return jsonify({
                'response': f"I'm not confident about this answer. {fallback_action}",
                'source': 'fallback',
                'action': fallback_action,
                'confidence_score': confidence_score
            })
        
        return jsonify({
            'response': "I don't have information about that topic.",
            'source': 'default',
            'confidence_score': confidence_score
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'AI Settings API',
        'version': '1.0.0',
        'endpoints': {
            'templates': '/ai/templates',
            'training': '/ai/training',
            'fallback': '/ai/fallback',
            'office_hours': '/ai/office-hours',
            'status': '/ai/status',
            'query': '/ai/query'
        }
    })

# Initialize service after app context is available
with app.app_context():
    db.create_all()
    service.init_app(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    