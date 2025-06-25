from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.orm import Session
from pydantic import BaseModel
from enum import Enum as PyEnum

app = FastAPI(title="Booking Manager API")

# Database configuration
import os
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'bookings.db')}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ShiftStatus(str, PyEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    STANDBY = "standby"

class ShiftFlag(str, PyEnum):
    URGENT = "urgent"
    NO_SHOW_RISK = "no_show_risk"
    HIGH_PRIORITY = "high_priority"
    NORMAL = "normal"

class Shift(Base):
    __tablename__ = "shifts"
    
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(Enum(ShiftStatus))
    flag = Column(Enum(ShiftFlag))
    worker_id = Column(Integer, ForeignKey("workers.id"))
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    worker = relationship("Worker", back_populates="shifts")

class Worker(Base):
    __tablename__ = "workers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    status = Column(Boolean, default=True)  # True for available, False for unavailable
    is_standby = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    shifts = relationship("Shift", back_populates="worker")

# Pydantic Models
class WorkerBase(BaseModel):
    name: str
    status: bool = True
    is_standby: bool = False

class WorkerCreate(WorkerBase):
    pass

class WorkerResponse(WorkerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ShiftBase(BaseModel):
    start_time: datetime
    end_time: datetime
    status: ShiftStatus = ShiftStatus.ACTIVE
    flag: ShiftFlag = ShiftFlag.NORMAL
    worker_id: int
    notes: Optional[str] = None

class ShiftCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    worker_id: int
    flag: ShiftFlag = ShiftFlag.NORMAL
    notes: Optional[str] = None

class ShiftUpdate(BaseModel):
    status: Optional[ShiftStatus] = None
    flag: Optional[ShiftFlag] = None
    notes: Optional[str] = None

class ShiftResponse(ShiftBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency - SINGLE DEFINITION
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoints
@app.get("/shifts", response_model=List[ShiftResponse])
def get_shifts(
    db: Session = Depends(get_db),
    status: Optional[ShiftStatus] = None,
    flag: Optional[ShiftFlag] = None,
    worker_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    query = db.query(Shift)
    
    if status:
        query = query.filter(Shift.status == status)
    if flag:
        query = query.filter(Shift.flag == flag)
    if worker_id:
        query = query.filter(Shift.worker_id == worker_id)
    if start_date:
        query = query.filter(Shift.start_time >= start_date)
    if end_date:
        query = query.filter(Shift.end_time <= end_date)
    
    return query.all()

@app.post("/shifts", response_model=ShiftResponse)
def create_shift(shift: ShiftCreate, db: Session = Depends(get_db)):
    # Check if worker exists
    worker = db.query(Worker).filter(Worker.id == shift.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    db_shift = Shift(
        start_time=shift.start_time,
        end_time=shift.end_time,
        worker_id=shift.worker_id,
        flag=shift.flag,
        notes=shift.notes,
        status=ShiftStatus.ACTIVE
    )
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    return db_shift

@app.put("/shifts/{shift_id}", response_model=ShiftResponse)
def update_shift(shift_id: int, shift_update: ShiftUpdate, db: Session = Depends(get_db)):
    db_shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not db_shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    for key, value in shift_update.dict(exclude_unset=True).items():
        setattr(db_shift, key, value)
    
    db.commit()
    db.refresh(db_shift)
    return db_shift

@app.get("/workers", response_model=List[WorkerResponse])
def get_workers(
    db: Session = Depends(get_db),
    is_standby: Optional[bool] = None,
    is_available: Optional[bool] = None
):
    query = db.query(Worker)
    
    if is_standby is not None:
        query = query.filter(Worker.is_standby == is_standby)
    if is_available is not None:
        query = query.filter(Worker.status == is_available)
    
    return query.all()

@app.post("/workers", response_model=WorkerResponse)
def create_worker(worker: WorkerCreate, db: Session = Depends(get_db)):
    db_worker = Worker(**worker.dict())
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)
    return db_worker

@app.post("/workers/{worker_id}/assign-shift", response_model=ShiftResponse)
def assign_shift_to_worker(
    worker_id: int,
    shift_id: int,
    db: Session = Depends(get_db)
):
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    shift.worker_id = worker_id
    db.commit()
    db.refresh(shift)
    return shift

@app.get("/shifts/available-workers", response_model=List[WorkerResponse])
def get_available_workers(
    shift_start: datetime,
    shift_end: datetime,
    db: Session = Depends(get_db)
):
    # Get workers who are available during the shift time
    available_workers = db.query(Worker).filter(
        Worker.status == True  # Available workers
    ).all()
    
    # Filter out workers who have conflicting shifts
    conflicting_worker_ids = db.query(Shift.worker_id).filter(
        Shift.start_time < shift_end,
        Shift.end_time > shift_start,
        Shift.status == ShiftStatus.ACTIVE
    ).distinct().all()
    
    conflicting_ids = [row[0] for row in conflicting_worker_ids]
    
    return [
        worker for worker in available_workers
        if worker.id not in conflicting_ids
    ]

def populate_test_data():
    """Populate some test data for testing"""
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(Worker).count() > 0:
            return
            
        # Create test workers
        workers = [
            Worker(name="John Doe", status=True, is_standby=False),
            Worker(name="Jane Smith", status=True, is_standby=True),
            Worker(name="Bob Johnson", status=False, is_standby=False)
        ]
        db.add_all(workers)
        db.commit()
        
        # Create test shifts
        now = datetime.now()
        shifts = [
            Shift(
                start_time=now + timedelta(hours=1),
                end_time=now + timedelta(hours=3),
                status=ShiftStatus.ACTIVE,
                flag=ShiftFlag.NORMAL,
                worker_id=1,
                notes="Morning shift"
            ),
            Shift(
                start_time=now + timedelta(hours=4),
                end_time=now + timedelta(hours=6),
                status=ShiftStatus.STANDBY,
                flag=ShiftFlag.URGENT,
                worker_id=2,
                notes="Afternoon shift"
            )
        ]
        db.add_all(shifts)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Populate test data
    populate_test_data()
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8002)