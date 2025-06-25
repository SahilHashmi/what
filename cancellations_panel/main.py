from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from pydantic import BaseModel
from enum import Enum as PyEnum

app = FastAPI(title="Cancellations Panel API")

# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./cancellations.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ShiftStatus(str, PyEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    STANDBY = "standby"

class Shift(Base):
    __tablename__ = "shifts"
    
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(Enum(ShiftStatus))
    worker_id = Column(Integer, ForeignKey("workers.id"))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    worker = relationship("Worker", back_populates="shifts")
    cancellations = relationship("Cancellation", back_populates="shift")
    rebooking_suggestions = relationship("QuickRebookingSuggestion", back_populates="shift")

class Worker(Base):
    __tablename__ = "workers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    status = Column(Boolean, default=True)
    is_standby = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    shifts = relationship("Shift", back_populates="worker")
    cancellations = relationship("Cancellation", back_populates="worker")
    blacklist_entries = relationship("BlacklistedWorker", back_populates="worker")
    rebooking_suggestions = relationship("QuickRebookingSuggestion", back_populates="worker")

class CancellationReason(str, PyEnum):
    NO_SHOW = "no_show"
    LATE_CANCELLATION = "late_cancellation"
    UNEXPECTED = "unexpected"
    SCHEDULE_CONFLICT = "schedule_conflict"
    OTHER = "other"

class CancellationStatus(str, PyEnum):
    PENDING = "pending"
    AUTO_REPLIED = "auto_replied"
    MANUAL_RESPONSE = "manual_response"
    BLACKLISTED = "blacklisted"

class CancellationReason(str, PyEnum):
    NO_SHOW = "no_show"
    LATE_CANCELLATION = "late_cancellation"
    UNEXPECTED = "unexpected"
    SCHEDULE_CONFLICT = "schedule_conflict"
    OTHER = "other"

class CancellationStatus(str, PyEnum):
    PENDING = "pending"
    AUTO_REPLIED = "auto_replied"
    MANUAL_RESPONSE = "manual_response"
    BLACKLISTED = "blacklisted"

class Cancellation(Base):
    __tablename__ = "cancellations"
    
    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"))
    worker_id = Column(Integer, ForeignKey("workers.id"))
    cancellation_time = Column(DateTime)
    reason = Column(Enum(CancellationReason))
    reason_detail = Column(Text)
    status = Column(Enum(CancellationStatus))
    auto_reply_sent = Column(Boolean, default=False)
    fallback_handled = Column(Boolean, default=False)
    blacklisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    shift = relationship("Shift", back_populates="cancellations")
    worker = relationship("Worker", back_populates="cancellations")

class BlacklistedWorker(Base):
    __tablename__ = "blacklisted_workers"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"))
    reason = Column(Text)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    worker = relationship("Worker", back_populates="blacklist_entries")

class QuickRebookingSuggestion(Base):
    __tablename__ = "rebooking_suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    original_shift_id = Column(Integer, ForeignKey("shifts.id"))
    suggested_worker_id = Column(Integer, ForeignKey("workers.id"))
    suggestion_time = Column(DateTime, default=datetime.utcnow)
    accepted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    shift = relationship("Shift", back_populates="rebooking_suggestions")
    worker = relationship("Worker", back_populates="rebooking_suggestions")

class CancellationCreate(BaseModel):
    shift_id: int
    worker_id: int
    reason: CancellationReason
    reason_detail: Optional[str] = None
    cancellation_time: Optional[datetime] = None

    class Config:
        from_attributes = True

class CancellationResponse(BaseModel):
    id: int
    shift_id: int
    worker_id: int
    cancellation_time: datetime
    reason: CancellationReason
    reason_detail: Optional[str]
    status: CancellationStatus
    auto_reply_sent: bool
    fallback_handled: bool
    blacklisted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CancellationResponse(BaseModel):
    id: int
    shift_id: int
    worker_id: int
    cancellation_time: datetime
    reason: CancellationReason
    reason_detail: Optional[str]
    status: CancellationStatus
    auto_reply_sent: bool
    fallback_handled: bool
    blacklisted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QuickRebookingSuggestionCreate(BaseModel):
    original_shift_id: int
    suggested_worker_id: int
    suggestion_time: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuickRebookingSuggestionResponse(BaseModel):
    id: int
    original_shift_id: int
    suggested_worker_id: int
    suggestion_time: datetime
    accepted: bool
    created_at: datetime

    class Config:
        from_attributes = True

class QuickRebookingSuggestionResponse(BaseModel):
    id: int
    original_shift_id: int
    suggested_worker_id: int
    suggestion_time: datetime
    accepted: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def populate_test_data():
    """Populate some test data for testing"""
    db = SessionLocal()
    try:
        # Create test worker
        worker = Worker(
            name="Test Worker",
            status=True,
            is_standby=False
        )
        db.add(worker)
        db.commit()
        
        # Create test shift
        now = datetime.now()
        shift = Shift(
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=3),
            status=ShiftStatus.ACTIVE,
            worker_id=worker.id,
            notes="Test shift"
        )
        db.add(shift)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    populate_test_data()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WorkerCreate(BaseModel):
    name: str
    status: bool
    is_standby: bool

class WorkerResponse(BaseModel):
    id: int
    name: str
    status: bool
    is_standby: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ShiftCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    status: ShiftStatus
    worker_id: int
    notes: str

class ShiftResponse(BaseModel):
    id: int
    start_time: datetime
    end_time: datetime
    status: ShiftStatus
    worker_id: int
    notes: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Worker endpoints
@app.get("/workers", response_model=List[WorkerResponse])
async def get_workers(db: Session = Depends(get_db)):
    return db.query(Worker).all()

@app.post("/workers", response_model=WorkerResponse)
async def create_worker(worker: WorkerCreate, db: Session = Depends(get_db)):
    db_worker = Worker(**worker.model_dump())
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)
    return db_worker

# Shift endpoints
@app.get("/shifts", response_model=List[ShiftResponse])
async def get_shifts(db: Session = Depends(get_db)):
    return db.query(Shift).all()

@app.post("/shifts", response_model=ShiftResponse)
async def create_shift(shift: ShiftCreate, db: Session = Depends(get_db)):
    db_shift = Shift(**shift.model_dump())
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    return db_shift

@app.get("/cancellations", response_model=List[CancellationResponse])
async def get_cancellations(
    db: Session = Depends(get_db),
    status: Optional[CancellationStatus] = None,
    worker_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    query = db.query(Cancellation)
    
    if status:
        query = query.filter(Cancellation.status == status)
    if worker_id:
        query = query.filter(Cancellation.worker_id == worker_id)
    if start_date:
        query = query.filter(Cancellation.cancellation_time >= start_date)
    if end_date:
        query = query.filter(Cancellation.cancellation_time <= end_date)
    
    return query.all()

@app.post("/cancellations", response_model=CancellationResponse)
async def create_cancellation(
    cancellation: CancellationCreate,
    db: Session = Depends(get_db)
):
    # Set cancellation time if not provided
    if cancellation.cancellation_time is None:
        cancellation.cancellation_time = datetime.utcnow()
    
    db_cancellation = Cancellation(**cancellation.model_dump())
    db.add(db_cancellation)
    db.commit()
    db.refresh(db_cancellation)
    
    # Auto-reply handling
    if db_cancellation.reason in [CancellationReason.NO_SHOW, CancellationReason.LATE_CANCELLATION]:
        db_cancellation.status = CancellationStatus.AUTO_REPLIED
        db_cancellation.auto_reply_sent = True
        db.commit()
        db.refresh(db_cancellation)
    
    return db_cancellation

@app.put("/cancellations/{cancellation_id}/blacklist", response_model=CancellationResponse)
async def blacklist_worker(
    cancellation_id: int,
    db: Session = Depends(get_db)
):
    cancellation = db.query(Cancellation).filter(Cancellation.id == cancellation_id).first()
    if not cancellation:
        raise HTTPException(status_code=404, detail="Cancellation not found")
    
    cancellation.blacklisted = True
    cancellation.status = CancellationStatus.BLACKLISTED
    
    # Create blacklist entry
    blacklist_entry = BlacklistedWorker(
        worker_id=cancellation.worker_id,
        reason=f"Multiple cancellations detected: {cancellation.reason}"
    )
    db.add(blacklist_entry)
    
    db.commit()
    db.refresh(cancellation)
    return cancellation

@app.post("/rebooking-suggestions", response_model=QuickRebookingSuggestionResponse)
async def create_rebooking_suggestion(
    suggestion: QuickRebookingSuggestionCreate,
    db: Session = Depends(get_db)
):
    # Set suggestion time if not provided
    if suggestion.suggestion_time is None:
        suggestion.suggestion_time = datetime.utcnow()
    
    db_suggestion = QuickRebookingSuggestion(**suggestion.model_dump())
    db.add(db_suggestion)
    db.commit()
    db.refresh(db_suggestion)
    return db_suggestion

@app.get("/rebooking-suggestions", response_model=List[QuickRebookingSuggestionResponse])
async def get_rebooking_suggestions(
    db: Session = Depends(get_db),
    original_shift_id: Optional[int] = None,
    accepted: Optional[bool] = None
):
    query = db.query(QuickRebookingSuggestion)
    
    if original_shift_id:
        query = query.filter(QuickRebookingSuggestion.original_shift_id == original_shift_id)
    if accepted is not None:
        query = query.filter(QuickRebookingSuggestion.accepted == accepted)
    
    return query.all()

if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(app, host="127.0.0.1", port=8005)
    #://127.0.0.1:8004