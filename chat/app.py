from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date
from enum import Enum
import json
import csv
import io
from uuid import uuid4

# Initialize FastAPI app
app = FastAPI(
    title="Conversation Log CRM API",
    description="API for managing conversation logs with filtering and export capabilities",
    version="1.0.0"
)

# Enums for conversation types and statuses
class ConversationType(str, Enum):
    BOOKING = "booking"
    CANCELLATION = "cancellation"
    STANDBY = "standby"
    INQUIRY = "inquiry"

class ConversationStatus(str, Enum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    ESCALATED = "escalated"

# Pydantic Models
class ConversationLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: ConversationType
    status: ConversationStatus
    worker_name: str
    client_name: str
    conversation_content: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high"] = "medium"

class ConversationCreate(BaseModel):
    type: ConversationType
    status: ConversationStatus
    worker_name: str
    client_name: str
    conversation_content: str
    tags: Optional[List[str]] = Field(default_factory=list)
    priority: Optional[Literal["low", "medium", "high"]] = "medium"

class ConversationUpdate(BaseModel):
    type: Optional[ConversationType] = None
    status: Optional[ConversationStatus] = None
    worker_name: Optional[str] = None
    client_name: Optional[str] = None
    conversation_content: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[Literal["low", "medium", "high"]] = None

class ConversationFilter(BaseModel):
    type: Optional[ConversationType] = None
    status: Optional[ConversationStatus] = None
    worker_name: Optional[str] = None
    client_name: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    tags: Optional[List[str]] = None

# In-memory storage (replace with database in production)
conversations_db: List[ConversationLog] = []

# Sample data for demonstration
sample_conversations = [
    ConversationLog(
        type=ConversationType.BOOKING,
        status=ConversationStatus.RESOLVED,
        worker_name="John Smith",
        client_name="Alice Johnson",
        conversation_content="Client requested booking for 2 guests on Dec 15th. Confirmed reservation #12345.",
        tags=["urgent", "vip-client"],
        priority="high"
    ),
    ConversationLog(
        type=ConversationType.CANCELLATION,
        status=ConversationStatus.UNRESOLVED,
        worker_name="Sarah Davis",
        client_name="Bob Wilson",
        conversation_content="Client wants to cancel booking due to emergency. Waiting for manager approval.",
        tags=["refund-required"],
        priority="medium"
    ),
    ConversationLog(
        type=ConversationType.INQUIRY,
        status=ConversationStatus.ESCALATED,
        worker_name="Mike Brown",
        client_name="Carol Taylor",
        conversation_content="Client inquiring about corporate rates. Complex pricing structure needed.",
        tags=["corporate", "pricing"],
        priority="high"
    )
]
conversations_db.extend(sample_conversations)

# Helper Functions
def filter_conversations(conversations: List[ConversationLog], filters: ConversationFilter) -> List[ConversationLog]:
    """Filter conversations based on provided criteria"""
    filtered = conversations
    
    if filters.type:
        filtered = [c for c in filtered if c.type == filters.type]
    
    if filters.status:
        filtered = [c for c in filtered if c.status == filters.status]
    
    if filters.worker_name:
        filtered = [c for c in filtered if filters.worker_name.lower() in c.worker_name.lower()]
    
    if filters.client_name:
        filtered = [c for c in filtered if filters.client_name.lower() in c.client_name.lower()]
    
    if filters.priority:
        filtered = [c for c in filtered if c.priority == filters.priority]
    
    if filters.date_from:
        filtered = [c for c in filtered if c.created_at.date() >= filters.date_from]
    
    if filters.date_to:
        filtered = [c for c in filtered if c.created_at.date() <= filters.date_to]
    
    if filters.tags:
        filtered = [c for c in filtered if any(tag in c.tags for tag in filters.tags)]
    
    return filtered

# API Endpoints

@app.get("/")
async def root():
    """API health check"""
    return {"message": "Conversation Log CRM API is running", "version": "1.0.0"}

@app.get("/conversations", response_model=List[ConversationLog])
async def get_conversations(
    type: Optional[ConversationType] = Query(None, description="Filter by conversation type"),
    status: Optional[ConversationStatus] = Query(None, description="Filter by status"),
    worker_name: Optional[str] = Query(None, description="Filter by worker name"),
    client_name: Optional[str] = Query(None, description="Filter by client name"),
    date_from: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    priority: Optional[Literal["low", "medium", "high"]] = Query(None, description="Filter by priority"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Get filtered conversation logs with pagination"""
    filters = ConversationFilter(
        type=type,
        status=status,
        worker_name=worker_name,
        client_name=client_name,
        date_from=date_from,
        date_to=date_to,
        priority=priority
    )
    
    filtered_conversations = filter_conversations(conversations_db, filters)
    
    # Apply pagination
    paginated_conversations = filtered_conversations[offset:offset + limit]
    
    return paginated_conversations

@app.get("/conversations/{conversation_id}", response_model=ConversationLog)
async def get_conversation(conversation_id: str):
    """Get a specific conversation by ID"""
    conversation = next((c for c in conversations_db if c.id == conversation_id), None)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.post("/conversations", response_model=ConversationLog)
async def create_conversation(conversation: ConversationCreate):
    """Create a new conversation log"""
    new_conversation = ConversationLog(**conversation.dict())
    conversations_db.append(new_conversation)
    return new_conversation

@app.put("/conversations/{conversation_id}", response_model=ConversationLog)
async def update_conversation(conversation_id: str, updates: ConversationUpdate):
    """Update an existing conversation"""
    conversation = next((c for c in conversations_db if c.id == conversation_id), None)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(conversation, field, value)
    
    conversation.updated_at = datetime.now()
    
    if updates.status == ConversationStatus.RESOLVED and not conversation.resolved_at:
        conversation.resolved_at = datetime.now()
    
    return conversation

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    global conversations_db
    conversations_db = [c for c in conversations_db if c.id != conversation_id]
    return {"message": "Conversation deleted successfully"}

@app.get("/conversations/export/csv")
async def export_conversations_csv(
    type: Optional[ConversationType] = Query(None),
    status: Optional[ConversationStatus] = Query(None),
    worker_name: Optional[str] = Query(None),
    client_name: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    priority: Optional[Literal["low", "medium", "high"]] = Query(None)
):
    """Export filtered conversations as CSV"""
    filters = ConversationFilter(
        type=type,
        status=status,
        worker_name=worker_name,
        client_name=client_name,
        date_from=date_from,
        date_to=date_to,
        priority=priority
    )
    
    filtered_conversations = filter_conversations(conversations_db, filters)
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = [
        "ID", "Type", "Status", "Worker Name", "Client Name", 
        "Created At", "Updated At", "Resolved At", "Priority", 
        "Tags", "Conversation Content"
    ]
    writer.writerow(headers)
    
    # Write data
    for conv in filtered_conversations:
        writer.writerow([
            conv.id,
            conv.type.value,
            conv.status.value,
            conv.worker_name,
            conv.client_name,
            conv.created_at.isoformat(),
            conv.updated_at.isoformat() if conv.updated_at else "",
            conv.resolved_at.isoformat() if conv.resolved_at else "",
            conv.priority,
            ";".join(conv.tags),
            conv.conversation_content
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=conversation_logs.csv"}
    )

@app.get("/conversations/export/json")
async def export_conversations_json(
    type: Optional[ConversationType] = Query(None),
    status: Optional[ConversationStatus] = Query(None),
    worker_name: Optional[str] = Query(None),
    client_name: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    priority: Optional[Literal["low", "medium", "high"]] = Query(None)
):
    """Export filtered conversations as JSON"""
    filters = ConversationFilter(
        type=type,
        status=status,
        worker_name=worker_name,
        client_name=client_name,
        date_from=date_from,
        date_to=date_to,
        priority=priority
    )
    
    filtered_conversations = filter_conversations(conversations_db, filters)
    
    # Convert to JSON
    json_data = json.dumps(
        [conv.dict() for conv in filtered_conversations],
        default=str,
        indent=2
    )
    
    return StreamingResponse(
        io.BytesIO(json_data.encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=conversation_logs.json"}
    )

@app.get("/stats/summary")
async def get_conversation_stats():
    """Get summary statistics of conversations"""
    total_conversations = len(conversations_db)
    
    # Count by type
    type_counts = {}
    for conv_type in ConversationType:
        type_counts[conv_type.value] = len([c for c in conversations_db if c.type == conv_type])
    
    # Count by status
    status_counts = {}
    for status in ConversationStatus:
        status_counts[status.value] = len([c for c in conversations_db if c.status == status])
    
    # Count by priority
    priority_counts = {
        "low": len([c for c in conversations_db if c.priority == "low"]),
        "medium": len([c for c in conversations_db if c.priority == "medium"]),
        "high": len([c for c in conversations_db if c.priority == "high"])
    }
    
    return {
        "total_conversations": total_conversations,
        "by_type": type_counts,
        "by_status": status_counts,
        "by_priority": priority_counts
    }

# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)