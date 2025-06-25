from ast import Str
import sys
import os
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel 
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, func, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from enum import Enum
from sqlalchemy.exc import SQLAlchemyError
import json

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize database
SQLALCHEMY_DATABASE_URL = "sqlite:///./dashboard.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create FastAPI app
app = FastAPI(title="Booking System Dashboard API")

# Define database models
class BookingStatus(str, Enum):
    confirmed = "confirmed"
    cancelled = "cancelled"
    standby = "standby"
    pending = "pending"
    completed = "completed"

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    response_time = Column(Float)  # in seconds
    agent_id = Column(String)
    customer_id = Column(String)
    service_type = Column(String)
    amount = Column(Float)
    reason = Column(String, nullable=True)

class AgentActivity(Base):
    __tablename__ = "agent_activity"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String)
    activity_type = Column(String)  # login, logout, message, booking, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration = Column(Float)  # in seconds

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)  # error, warning, info
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    severity = Column(Integer)  # 1-5, 5 being most severe
    resolved = Column(Boolean, default=False)

# Add custom report model
class CustomReportModel(Base):
    __tablename__ = "custom_reports"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    metrics = Column(String)  # JSON string of metrics
    filters = Column(String)  # JSON string of filters
    data = Column(String)  # JSON string of report data

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for API responses
class BookingStats(BaseModel):
    total: int
    confirmed: int
    cancelled: int
    standby: int
    pending: int
    completed: int
    avg_response_time: float
    revenue: float

class CancellationStats(BaseModel):
    total: int
    today: int
    reasons: Dict[str, int]
    repeat_cancellers: List[Dict[str, Any]]

class WorkerStats(BaseModel):
    total_workers: int
    available: int
    standby: int
    busy: int
    top_performers: List[Dict[str, Any]]

class ChatStats(BaseModel):
    total_messages: int
    unread_messages: int
    active_conversations: int
    avg_response_time: float
    top_agents: List[Dict[str, Any]]

class AlertResponse(BaseModel):
    id: int
    type: str
    message: str
    timestamp: datetime
    severity: int
    resolved: bool

class DashboardOverview(BaseModel):
    timestamp: datetime
    booking_stats: BookingStats
    cancellation_stats: CancellationStats
    worker_stats: WorkerStats
    chat_stats: ChatStats
    alerts: List[AlertResponse]

class CustomReportParams(BaseModel):
    start_date: str
    end_date: str
    metrics: List[str]  # Available metrics: bookings, cancellations, workers, chat, revenue
    group_by: str  # day, week, month
    filters: Optional[Dict[str, Any]] = None

class CustomReportResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    metrics: List[str]
    filters: Dict[str, Any]
    data: Dict[str, Any]

@app.get("/dashboard/overview", response_model=DashboardOverview)
async def get_dashboard_overview(db: Session = Depends(get_db)):
    """Get comprehensive dashboard overview with all metrics"""
    try:
        # Get today's date
        today = datetime.utcnow().date()
        
        # Query booking stats
        total_bookings = db.query(func.count(Booking.id)).scalar() or 0
        confirmed_bookings = db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.confirmed).scalar() or 0
        cancelled_bookings = db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.cancelled).scalar() or 0
        standby_bookings = db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.standby).scalar() or 0
        pending_bookings = db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.pending).scalar() or 0
        completed_bookings = db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.completed).scalar() or 0
        avg_response_time = db.query(func.avg(Booking.response_time)).scalar() or 0
        total_revenue = db.query(func.sum(Booking.amount)).filter(Booking.status == BookingStatus.confirmed).scalar() or 0
        
        # Query cancellation stats
        today_cancellations = db.query(func.count(Booking.id)).filter(
            Booking.status == BookingStatus.cancelled,
            func.date(Booking.created_at) == today
        ).scalar() or 0
        
        # Get cancellation reasons
        reasons_query = db.query(Booking.reason, func.count(Booking.id)).\
            filter(Booking.status == BookingStatus.cancelled, Booking.reason.isnot(None)).\
            group_by(Booking.reason).all()
        reasons = {reason: count for reason, count in reasons_query}
        
        # Query worker stats
        total_workers = db.query(func.count(func.distinct(Booking.agent_id))).scalar() or 0
        
        # Get top performers
        top_performers_query = db.query(
            Booking.agent_id,
            func.count(Booking.id).label('booking_count')
        ).group_by(Booking.agent_id).order_by(func.count(Booking.id).desc()).limit(5).all()
        
        top_performers = [
            {
                'agent_id': agent_id,
                'booking_count': booking_count
            }
            for agent_id, booking_count in top_performers_query
        ]
        
        # Query alerts
        active_alerts_query = db.query(Alert).filter(Alert.resolved == False).all()
        active_alerts = [
            AlertResponse(
                id=alert.id,
                type=alert.type,
                message=alert.message,
                timestamp=alert.timestamp,
                severity=alert.severity,
                resolved=alert.resolved
            )
            for alert in active_alerts_query
        ]
        
        return DashboardOverview(
            timestamp=datetime.utcnow(),
            booking_stats=BookingStats(
                total=total_bookings,
                confirmed=confirmed_bookings,
                cancelled=cancelled_bookings,
                standby=standby_bookings,
                pending=pending_bookings,
                completed=completed_bookings,
                avg_response_time=avg_response_time,
                revenue=total_revenue
            ),
            cancellation_stats=CancellationStats(
                total=cancelled_bookings,
                today=today_cancellations,
                reasons=reasons,
                repeat_cancellers=[]  # TODO: Implement repeat canceller logic
            ),
            worker_stats=WorkerStats(
                total_workers=total_workers,
                available=0,  # TODO: Implement availability logic
                standby=0,  # TODO: Implement standby logic
                busy=0,  # TODO: Implement busy status logic
                top_performers=top_performers
            ),
            chat_stats=ChatStats(
                total_messages=0,  # TODO: Implement chat integration
                unread_messages=0,  # TODO: Implement chat integration
                active_conversations=0,  # TODO: Implement chat integration
                avg_response_time=0,  # TODO: Implement chat integration
                top_agents=[]  # TODO: Implement chat integration
            ),
            alerts=active_alerts
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching dashboard overview: {str(e)}"
        )

@app.post("/dashboard/reports", response_model=CustomReportResponse)
async def create_custom_report(params: CustomReportParams, db: Session = Depends(get_db)):
    """Create a custom report with specified metrics and filters"""
    try:
        # Create new report
        new_report = CustomReportModel(
            title=f"Custom Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            metrics=json.dumps(params.metrics),
            filters=json.dumps(params.filters or {}),
            data=json.dumps({})  # TODO: Generate actual report data
        )
        
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        return CustomReportResponse(
            id=new_report.id,
            title=new_report.title,
            created_at=new_report.created_at,
            metrics=json.loads(new_report.metrics),
            filters=json.loads(new_report.filters),
            data=json.loads(new_report.data)
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating report: {str(e)}")

@app.get("/dashboard/reports/{report_id}", response_model=CustomReportResponse)
async def get_custom_report(report_id: int, db: Session = Depends(get_db)):
    """Get a specific custom report"""
    try:
        report = db.query(CustomReportModel).filter(CustomReportModel.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return CustomReportResponse(
            id=report.id,
            title=report.title,
            created_at=report.created_at,
            metrics=json.loads(report.metrics),
            filters=json.loads(report.filters),
            data=json.loads(report.data)
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching report: {str(e)}")

@app.get("/dashboard/alerts", response_model=List[AlertResponse])
async def get_alerts(db: Session = Depends(get_db)):
    """Get all active alerts"""
    try:
        alerts = db.query(Alert).filter(Alert.resolved == False).order_by(
            Alert.severity.desc(), Alert.timestamp.desc()
        ).all()
        
        return [
            AlertResponse(
                id=alert.id,
                type=alert.type,
                message=alert.message,
                timestamp=alert.timestamp,
                severity=alert.severity,
                resolved=alert.resolved
            )
            for alert in alerts
        ]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/dashboard/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Resolve an alert"""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.resolved = True
        db.commit()
        return {"status": "resolved", "message": "Alert resolved successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/dashboard/metrics/bookings", response_model=BookingStats)
async def get_booking_metrics(db: Session = Depends(get_db)):
    """Get detailed booking metrics"""
    try:
        total = db.query(func.count(Booking.id)).scalar() or 0
        confirmed = db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.confirmed).scalar() or 0
        cancelled = db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.cancelled).scalar() or 0
        standby = db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.standby).scalar() or 0
        pending = db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.pending).scalar() or 0
        completed = db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.completed).scalar() or 0
        avg_response_time = db.query(func.avg(Booking.response_time)).scalar() or 0
        revenue = db.query(func.sum(Booking.amount)).filter(Booking.status == BookingStatus.confirmed).scalar() or 0
        
        return BookingStats(
            total=total,
            confirmed=confirmed,
            cancelled=cancelled,
            standby=standby,
            pending=pending,
            completed=completed,
            avg_response_time=avg_response_time,
            revenue=revenue
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/dashboard/metrics/cancellations", response_model=CancellationStats)
async def get_cancellation_metrics(db: Session = Depends(get_db)):
    """Get detailed cancellation metrics"""
    try:
        total = db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.cancelled).scalar() or 0
        today = datetime.utcnow().date()
        today_cancellations = db.query(func.count(Booking.id)).filter(
            Booking.status == BookingStatus.cancelled,
            func.date(Booking.created_at) == today
        ).scalar() or 0
        
        # Get reasons distribution
        reasons_query = db.query(Booking.reason, func.count(Booking.id)).\
            filter(Booking.status == BookingStatus.cancelled, Booking.reason.isnot(None)).\
            group_by(Booking.reason).all()
        reasons = {reason: count for reason, count in reasons_query}
        
        return CancellationStats(
            total=total,
            today=today_cancellations,
            reasons=reasons,
            repeat_cancellers=[]  # TODO: Implement repeat canceller logic
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/dashboard/metrics/workers", response_model=WorkerStats)
async def get_worker_metrics(db: Session = Depends(get_db)):
    """Get detailed worker metrics"""
    try:
        total_workers = db.query(func.count(func.distinct(Booking.agent_id))).scalar() or 0
        
        # Get top performers
        top_performers_query = db.query(
            Booking.agent_id,
            func.count(Booking.id).label('booking_count')
        ).group_by(Booking.agent_id).order_by(func.count(Booking.id).desc()).limit(5).all()
        
        top_performers = [
            {
                'agent_id': agent_id,
                'booking_count': booking_count
            }
            for agent_id, booking_count in top_performers_query
        ]
        
        return WorkerStats(
            total_workers=total_workers,
            available=0,  # TODO: Implement availability logic
            standby=0,
            busy=0,
            top_performers=top_performers
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
#===============================================================
@app.get("/dashboard/activity/bookings")
async def booking_activity_chart(db: Session = Depends(get_db)):
    try:
        results = db.query(
            func.strftime("%w", Booking.created_at).label("day"),  # '0' = Sunday
            Booking.status,
            func.count(Booking.id)
        ).group_by("day", Booking.status).all()

        activity = {"Mon": {}, "Tue": {}, "Wed": {}, "Thu": {}, "Fri": {}, "Sat": {}, "Sun": {}}
        days_map = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        for day, status, count in results:
            day_name = days_map[int(day)]
            activity[day_name][status] = count

        return activity
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import gspread
from oauth2client.service_account import ServiceAccountCredentials

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1c2b6L3-8UcMi8jFie8-LQetE37inpObKh_tAWWCDyYk"

def update_google_sheet(row_data: list):
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name("google-credentials.json", scope)
        client = gspread.authorize(creds)

        # Open the correct worksheet (first one)
        sheet = client.open_by_url(SPREADSHEET_URL)
        worksheet = sheet.get_worksheet(0)  # Or use: sheet.worksheet("Sheet1")

        worksheet.append_row(row_data)
        return True
    except Exception as e:
        print(f"[❌ Google Sheet Error] {e}")
        return False



@app.get("/dashboard/metrics/whatsapp")
async def get_whatsapp_volume():
    # Simulated hourly message volume
    hours = ["6am", "9am", "12pm", "3pm", "6pm", "9pm"]
    messages = [4, 7, 6, 9, 14, 8]

    return {"labels": hours, "message_volume": messages}

@app.get("/dashboard/metrics/agent-activity")
async def get_agent_activity(db: Session = Depends(get_db)):
    try:
        total_msgs = db.query(func.count(AgentActivity.id)).filter(
            AgentActivity.activity_type == "message"
        ).scalar() or 0

        auto_responses = db.query(func.count(AgentActivity.id)).filter(
            AgentActivity.activity_type == "message",
            AgentActivity.duration < 5  # Assuming fast response is automated
        ).scalar() or 0

        rate = (auto_responses / total_msgs) * 100 if total_msgs > 0 else 0

        return {"auto_response_rate": round(rate, 2), "total_messages": total_msgs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class WhatsAppMessage(BaseModel):
    worker_name: str
    outlet: str
    shift_date: str
    shift_time: str
    request_type: str

# 📤 API Endpoint to Receive WhatsApp Request
@app.post("/webhook/whatsapp")
def handle_message(data: WhatsAppMessage):
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.worker_name,
        data.outlet,
        data.shift_date,
        data.shift_time,
        data.request_type,
        "Notified"
    ]
    success = update_google_sheet(row)
    if success:
        return {"status": "success", "message": "Google Sheet updated ✅"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update Google Sheet ❌")

#========================================================

@app.get("/dashboard/metrics/chat", response_model=ChatStats)
async def get_chat_metrics():
    """Get detailed chat metrics"""
    # Currently returns dummy data since chat integration is not complete
    return ChatStats(
        total_messages=0,
        unread_messages=0,
        active_conversations=0,
        avg_response_time=0,
        top_agents=[]
    )

def populate_test_data():
    """Populate database with test data"""
    db = SessionLocal()
    try:
        # Clear existing data
        db.query(Alert).delete()
        db.query(AgentActivity).delete()
        db.query(Booking).delete()
        db.commit()
        
        # Create some test bookings
        test_bookings = [
            Booking(
                status="confirmed",
                response_time=120.5,
                agent_id="agent1",
                customer_id="cust1",
                service_type="hotel",
                amount=1500.0
            ),
            Booking(
                status="cancelled",
                response_time=90.2,
                agent_id="agent2",
                customer_id="cust2",
                service_type="flight",
                amount=2500.0,
                reason="customer_request"
            ),
            Booking(
                status="standby",
                response_time=150.3,
                agent_id="agent1",
                customer_id="cust3",
                service_type="hotel",
                amount=1200.0
            ),
            Booking(
                status="pending",
                response_time=60.1,
                agent_id="agent3",
                customer_id="cust4",
                service_type="car",
                amount=500.0
            ),
            Booking(
                status="completed",
                response_time=80.0,
                agent_id="agent1",
                customer_id="cust5",
                service_type="hotel",
                amount=1800.0
            )
        ]
        
        # Create some agent activity
        test_activities = [
            AgentActivity(
                agent_id="agent1",
                activity_type="login",
                duration=300.0
            ),
            AgentActivity(
                agent_id="agent2",
                activity_type="message",
                duration=60.0
            ),
            AgentActivity(
                agent_id="agent3",
                activity_type="booking",
                duration=120.0
            )
        ]
        
        # Create some alerts
        test_alerts = [
            Alert(
                type="error",
                message="Failed to send reply to customer 123",
                severity=4
            ),
            Alert(
                type="warning",
                message="Unrecognized message from customer 456",
                severity=3
            ),
            Alert(
                type="info",
                message="System maintenance scheduled for tonight",
                severity=2
            )
        ]
        
        # Add to database
        db.add_all(test_bookings)
        db.add_all(test_activities)
        db.add_all(test_alerts)
        db.commit()
        
        print("Test data populated successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error populating test data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Populate test data
    populate_test_data()
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8004)