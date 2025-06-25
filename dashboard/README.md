# Dashboard Service

A FastAPI-based dashboard service that provides real-time analytics and monitoring for the booking platform.

## Features

1. **Real-time Monitoring**:
   - Active shifts overview
   - Worker availability status
   - Cancellation statistics
   - Chat activity metrics

2. **Analytics**:
   - Shift booking trends
   - Cancellation patterns
   - Worker performance metrics
   - Chat engagement analysis

3. **Alerts & Notifications**:
   - Urgent shift notifications
   - High cancellation rate alerts
   - Worker availability warnings
   - System health monitoring

4. **Reporting**:
   - Historical data analysis
   - Custom report generation
   - Export functionality
   - Performance tracking

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
uvicorn main:app --reload --port 8004
```

## API Endpoints

### Dashboard Metrics
- GET `/dashboard/metrics`: Get real-time metrics
- GET `/dashboard/history`: Get historical data
- GET `/dashboard/alerts`: Get active alerts
- GET `/dashboard/reports`: Generate reports

### Custom Reports
- POST `/dashboard/reports/custom`: Create custom reports
- GET `/dashboard/reports/{id}`: Retrieve reports
- POST `/dashboard/reports/export`: Export reports

## Usage

The dashboard service runs on port 8004 and provides RESTful API endpoints for dashboard metrics and reporting features.

## Dependencies

- FastAPI
- SQLAlchemy
- Python 3.10+
- Chart libraries for visualization
- Data processing libraries
