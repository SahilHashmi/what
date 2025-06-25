import unittest
from datetime import datetime, timedelta
from reports import app, db, Report, AnalyticsService

class TestReports(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_reports.db'
        self.app.config['TESTING'] = True
        
        with self.app.app_context():
            db.create_all()
            
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            os.remove('test_reports.db')

    def test_ai_response_rate(self):
        with self.app.app_context():
            service = AnalyticsService(app)
            start_date = datetime.utcnow() - timedelta(days=30)
            end_date = datetime.utcnow()
            
            result = service.get_ai_response_rate(start_date, end_date)
            self.assertIn('total_queries', result)
            self.assertIn('ai_handled', result)
            self.assertIn('success_rate', result)
            self.assertTrue(0 <= result['success_rate'] <= 100)

    def test_booking_fill_rate(self):
        with self.app.app_context():
            service = AnalyticsService(app)
            start_date = datetime.utcnow() - timedelta(days=30)
            end_date = datetime.utcnow()
            
            result = service.get_booking_fill_rate(start_date, end_date)
            self.assertIn('total_slots', result)
            self.assertIn('filled_slots', result)
            self.assertIn('fill_rate', result)
            self.assertTrue(0 <= result['fill_rate'] <= 100)

    def test_cancellation_trends(self):
        with self.app.app_context():
            service = AnalyticsService(app)
            start_date = datetime.utcnow() - timedelta(days=30)
            end_date = datetime.utcnow()
            
            result = service.get_cancellation_trends(start_date, end_date)
            self.assertIn('total_bookings', result)
            self.assertIn('cancellations', result)
            self.assertIn('reason_distribution', result)
            self.assertTrue(0 <= result['cancellation_rate'] <= 100)

    def test_peak_hours(self):
        with self.app.app_context():
            service = AnalyticsService(app)
            start_date = datetime.utcnow() - timedelta(days=30)
            end_date = datetime.utcnow()
            
            result = service.get_peak_hours(start_date, end_date)
            self.assertIn('peak_hours', result)
            self.assertIn('total_inquiries', result)
            self.assertIn('peak_hour', result)

    def test_export_csv(self):
        with self.app.app_context():
            service = AnalyticsService(app)
            test_data = {
                'date': ['2023-01-01', '2023-01-02'],
                'value': [100, 200]
            }
            
            csv_data = service.export_to_csv(test_data, 'test.csv')
            self.assertTrue(len(csv_data) > 0)

    def test_export_excel(self):
        with self.app.app_context():
            service = AnalyticsService(app)
            test_data = {
                'date': ['2023-01-01', '2023-01-02'],
                'value': [100, 200]
            }
            
            excel_data = service.export_to_excel(test_data, 'test.xlsx')
            self.assertTrue(len(excel_data) > 0)

if __name__ == '__main__':
    unittest.main()
