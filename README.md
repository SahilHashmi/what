# Booking Platform Services

A microservices-based booking platform with multiple independent services:

## Services Overview

1. **Booking Manager**
   - Port: 8002
   - Purpose: Manage shift bookings and worker assignments
   - Features: Shift management, worker assignments, status tracking

2. **Dashboard**
   - Port: 8003
   - Purpose: Analytics and metrics dashboard
   - Features: Booking stats, cancellation metrics, worker performance

3. **Cancellations Panel**
   - Port: 8004
   - Purpose: Manage booking cancellations
   - Features: Cancellation handling, reason tracking, analytics

4. **Chat**
   - Port: 8005
   - Purpose: Real-time chat functionality
   - Features: User messaging, chat history, notifications

5. **User Management**
   - Port: 8006
   - Purpose: User authentication and authorization
   - Features: User registration, login, role management

6. **AI Settings**
   - Port: 8007
   - Purpose: AI configuration and management
   - Features: AI model settings, parameter tuning

7. **Admin Controls**
   - Port: 8008
   - Purpose: Administrative functions
   - Features: System configuration, user management

8. **Monitoring**
   - Port: 8009
   - Purpose: System monitoring and health checks
   - Features: Performance metrics, error tracking

9. **Reports**
   - Port: 8010
   - Purpose: Report generation
   - Features: Custom reports, analytics export

10. **Standby**
    - Port: 8011
    - Purpose: Standby worker management
    - Features: Standby scheduling, availability tracking

## Deployment Instructions

### Render Deployment

1. **Prerequisites**
   - Render account
   - Git repository with the code
   - Python 3.11 (use python:3.11-slim for Docker)
     - Note: Python 3.13 is not recommended as some dependencies may not be compatible

2. **Files Required**
   - [requirements.txt](cci:7://file:///c:/Users/ashis/Watsapp/requirements.txt:0:0-0:0) - Python dependencies
   - [Procfile](cci:7://file:///c:/Users/ashis/Watsapp/Procfile:0:0-0:0) - Application startup configuration
   - [render.yaml](cci:7://file:///c:/Users/ashis/Watsapp/render.yaml:0:0-0:0) - Render deployment configuration
   - [main.py](cci:7://file:///c:/Users/ashis/Watsapp/main.py:0:0-0:0) - Main application file

3. **Deployment Steps**
   1. Push your code to a Git repository
   2. Create a new Web Service on Render
   3. Connect your Git repository
   4. Set the following environment variables:
      - `PORT`: Port number (default: 8000)
      - Add any database configuration if needed
   5. Deploy the application

4. **Health Check**
   - Path: `/health`
   - Timeout: 30 seconds
   - Interval: 10 seconds
   - Retries: 3
   - Initial delay: 10 seconds

5. **Monitoring**
   - Render provides built-in monitoring
   - Set up alerts in Render dashboard
   - Monitor logs through Render's log viewer

### Local Development

1. **Setup**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run the application
   uvicorn main:app --reload
   ```

2. **Testing**
   - API documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## API Endpoints

All endpoints are available through the unified API at:
- Base URL: `/`
- Booking: `/booking/`
- Dashboard: `/dashboard/`
- Cancellations: `/cancellations/`
- Chat: `/chat/`
- User Management: `/user/`
- AI Settings: `/ai/`
- Admin Controls: `/admin/`
- Monitoring: `/monitoring/`
- Reports: `/reports/`
- Standby: `/standby/`

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License](LICENSE)

1. **Booking Manager**
   - Port: 8002
   - Purpose: Manage shift bookings and worker assignments
   - Features:
     - Shift management
     - Worker availability tracking
     - Manual shift overrides
     - Standby worker suggestions

2. **Cancellations Panel**
   - Port: 8003
   - Purpose: Handle shift cancellations and rebooking
   - Features:
     - Cancellation tracking
     - AI-powered reason analysis
     - Automatic reply handling
     - Blacklisting repeat cancellers
     - Quick rebooking suggestions

3. **Chat Service**
   - Port: 8001
   - Purpose: Provide real-time communication
   - Features:
     - Real-time messaging
     - Message status tracking
     - Attachment support
     - Message export

4. **Dashboard Service**
   - Port: 8004
   - Purpose: Provide analytics and monitoring
   - Features:
     - Real-time metrics
     - Historical data analysis
     - Alert system
     - Custom reporting

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/AshishS1709/ADMIN-PANEL.git
```

2. Create virtual environment and install dependencies:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. Run each service:
```bash
# Booking Manager
cd booking_manager
uvicorn main:app --reload --port 8002

# Cancellations Panel
cd cancellations_panel
uvicorn main:app --reload --port 8003

# Chat Service
cd chat
uvicorn main:app --reload --port 8001

# Dashboard Service
cd dashboard
uvicorn main:app --reload --port 8004
```

## Project Structure
```
booking-platform/
├── booking_manager/
│   ├── main.py
│   ├── test_booking_manager.py
│   ├── requirements.txt
│   └── bookings.db
├── cancellations_panel/
│   ├── main.py
│   ├── test_cancellations.py
│   ├── requirements.txt
│   └── cancellations.db
├── chat/
│   ├── main.py
│   ├── test_chat.py
│   ├── requirements.txt
│   └── database.py
└── dashboard/
    ├── main.py
    ├── test_dashboard.py
    └── requirements.txt
```

## Technology Stack

- Backend: FastAPI
- Database: SQLite
- ORM: SQLAlchemy
- Testing: pytest
- Validation: Pydantic
- Python 3.10+

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here]
