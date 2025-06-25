import unittest
from datetime import datetime, timedelta
from admin_controls import app, db, AdminUser, IntegrationSetting, WhatsAppToken, DowntimeNotice, Role

class TestAdminControls(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_admin_controls.db'
        self.app.config['TESTING'] = True
        
        with self.app.app_context():
            db.create_all()
            
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            os.remove('test_admin_controls.db')

    def test_user_creation(self):
        with self.app.app_context():
            user = AdminUser(
                username='admin',
                password_hash='hashed_password',
                role=Role.SUPER_ADMIN
            )
            db.session.add(user)
            db.session.commit()
            
            self.assertIsNotNone(user.id)

    def test_integration_settings(self):
        with self.app.app_context():
            # Create setting
            setting = IntegrationSetting(
                name='Zapier Integration',
                provider='zapier',
                config={'api_key': 'test_key'},
                enabled=True
            )
            db.session.add(setting)
            db.session.commit()
            
            # Get setting
            settings = IntegrationSetting.query.all()
            self.assertEqual(len(settings), 1)
            
            # Update setting
            setting.enabled = False
            db.session.commit()
            
            updated = IntegrationSetting.query.get(setting.id)
            self.assertFalse(updated.enabled)

    def test_whatsapp_tokens(self):
        with self.app.app_context():
            # Create token
            token = WhatsAppToken(
                token='test_token',
                expires_at=datetime.utcnow() + timedelta(days=1)
            )
            db.session.add(token)
            db.session.commit()
            
            # Get token
            tokens = WhatsAppToken.query.all()
            self.assertEqual(len(tokens), 1)
            
            # Check validity
            self.assertTrue(tokens[0].is_valid())

    def test_downtime_notices(self):
        with self.app.app_context():
            # Create notice
            notice = DowntimeNotice(
                message='System maintenance',
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=2),
                created_by='admin'
            )
            db.session.add(notice)
            db.session.commit()
            
            # Get notice
            notices = DowntimeNotice.query.all()
            self.assertEqual(len(notices), 1)

if __name__ == '__main__':
    unittest.main()
