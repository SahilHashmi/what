# Chat Integration Service

A FastAPI-based chat system that provides real-time communication capabilities for the booking platform.

## Features

1. **Message Management**:
   - Send and receive messages
   - Track message status (sent, delivered, read)
   - Support for message attachments
   - Message search and filtering

2. **Real-time Communication**:
   - WebSocket support for instant updates
   - Message delivery notifications
   - Typing indicators
   - Read receipts

3. **Message Organization**:
   - Threaded conversations
   - Message categorization
   - Message history
   - Export functionality

4. **Security**:
   - Message encryption
   - User authentication
   - Access control
   - Message retention policies

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
uvicorn main:app --reload --port 8001
```

## API Endpoints

### Messages
- POST `/messages`: Create new message
- GET `/messages`: Retrieve messages with filters
- PATCH `/messages/{id}`: Update message status
- POST `/messages/attachments`: Upload attachments
- GET `/messages/export`: Export message logs

## Usage

The chat service runs on port 8001 and provides RESTful API endpoints for message management and real-time communication features.

## Dependencies

- FastAPI
- SQLAlchemy
- WebSocket
- Pydantic
- Python 3.10+
