# Cancellations Panel API

A FastAPI-based cancellations management system that handles:
- Cancellation tracking and management
- AI-powered cancellation reason analysis
- Automatic reply handling
- Blacklisting repeat cancellers
- Quick rebooking suggestions

## Features

1. **Cancellation Management**:
   - Track all shift cancellations
   - Record cancellation reasons
   - Capture detailed reason descriptions
   - Monitor cancellation patterns

2. **AI Integration**:
   - Automatic cancellation reason detection
   - Smart categorization of cancellations
   - Pattern recognition for repeat behavior

3. **Automatic Response Handling**:
   - Auto-reply to common cancellations
   - Fallback handling for complex cases
   - Status tracking for responses

4. **Blacklisting System**:
   - Identify repeat cancellers
   - Blacklist problematic workers
   - Track blacklisting reasons
   - Prevent future bookings

5. **Rebooking Suggestions**:
   - Smart rebooking recommendations
   - Quick suggestion generation
   - Worker availability checking
   - Suggestion acceptance tracking

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn main:app --reload --port 8003
```

## API Endpoints

### Cancellations
- `GET /cancellations` - List all cancellations with filters
- `POST /cancellations` - Create new cancellation
- `PUT /cancellations/{cancellation_id}/blacklist` - Blacklist worker

### Rebooking Suggestions
- `POST /rebooking-suggestions` - Create rebooking suggestion
- `GET /rebooking-suggestions` - List rebooking suggestions

## Testing

Run the test script:
```bash
python test_cancellations.py
```
