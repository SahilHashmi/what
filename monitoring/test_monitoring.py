import unittest
from datetime import datetime, timedelta
import os
from monitoring import app, db, MonitoringService, AutomationLog, MessageMatchRate, FailedQuery, DailyConversation

class TestMonitoring(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_monitoring.db'
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        with self.app.app_context():
            db.create_all()
            self.service = MonitoringService(self.app)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            os.remove('test_monitoring.db')

    def test_message_handling(self):
        with self.app.app_context():
            # Log a message handled by AI
            self.service.log_message_handling(
                message_id='123',
                handled_by='ai',
                confidence_score=0.95,
                response_time=1.2
            )
            
            # Log a message handled by human
            self.service.log_message_handling(
                message_id='456',
                handled_by='human',
                response_time=5.3
            )
            
            # Check logs
            logs = AutomationLog.query.all()
            self.assertEqual(len(logs), 2)
            
            # Check match rate
            rate = MessageMatchRate.query.first()
            self.assertEqual(rate.total_messages, 2)
            self.assertEqual(rate.auto_resolved, 1)
            self.assertEqual(rate.match_rate, 50.0)

    def test_failed_query(self):
        with self.app.app_context():
            self.service.log_failed_query(
                message="What are your hours?",
                intent="hours",
                actual_intent="operating_hours",
                confidence_score=0.3
            )
            
            query = FailedQuery.query.first()
            self.assertIsNotNone(query)
            self.assertEqual(query.confidence_score, 0.3)

    def test_conversation_stats(self):
        with self.app.app_context():
            # Log some messages
            for i in range(5):
                self.service.log_message_handling(
                    message_id=f'msg{i}',
                    handled_by='ai' if i % 2 == 0 else 'human',
                    response_time=1.5
                )
            
            # Update stats
            self.service.update_conversation_stats()
            
            stats = DailyConversation.query.first()
            self.assertIsNotNone(stats)
            self.assertEqual(stats.total_conversations, 5)
            self.assertGreater(stats.average_response_time, 0)

if __name__ == '__main__':
    unittest.main()
