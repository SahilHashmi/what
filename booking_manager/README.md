# Booking Manager API

A FastAPI-based booking management system that allows:
- View current & upcoming shift bookings
- Manual override or reassign shifts
- Auto-suggest available standby workers
- Tag shifts with flags (urgent, no-show risk)

## Features

- Shift Management:
  - Create, update, and delete shifts
  - Set shift status (active, completed, cancelled, standby)
  - Tag shifts with flags (urgent, no-show risk, high priority)
  - Add notes to shifts

- Worker Management:
  - Track worker availability
  - Mark workers as standby
  - View worker shift history
  - Assign shifts to workers

- Smart Scheduling:
  - Auto-suggest available workers for shifts
  - Prevent double booking
  - Show worker availability

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn main:app --reload --port 8002
```

## API Endpoints

### Shifts
- `GET /shifts` - List all shifts with optional filters
- `POST /shifts` - Create a new shift
- `PUT /shifts/{shift_id}` - Update shift details
- `GET /shifts/available-workers` - Get available workers for a shift

### Workers
- `GET /workers` - List all workers with optional filters
- `POST /workers/{worker_id}/assign-shift` - Assign a shift to a worker

## Testing

Run the test script:
```bash
python test_booking_manager.py
```
