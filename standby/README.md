# Standby List Manager

A web application for managing worker standby lists with features for viewing workers by date, location, and role, and managing shift assignments.

## Features

- View workers on standby by Date, Location, or Role
- Notify or auto-assign shifts
- AI status tracking (pending/confirmed)
- Worker reliability rating system

## Setup

1. Backend:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run the backend server
   python app.py
   ```

2. Frontend:
   ```bash
   # Navigate to frontend directory
   cd frontend
   
   # Install dependencies
   npm install
   
   # Start the development server
   npm start
   ```
