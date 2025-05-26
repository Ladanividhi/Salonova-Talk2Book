# Salon Booking Voice Assistant

An AI-powered voice assistant for booking salon appointments. The system uses speech recognition to interact with users and helps them book appointments at their preferred salon.

## Features

- Voice-based interaction
- Real-time availability checking
- Automatic slot suggestion if requested time is unavailable
- MongoDB integration for data persistence
- Support for multiple salons and services

## Prerequisites

- Python 3.8+
- MongoDB
- Node.js (for running the frontend)
- A microphone for voice input

## Installation

1. Install MongoDB and make sure it's running on localhost:27017

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database with sample data:
```bash
python backend/init_db.py
```

## Running the Application

1. Start the backend server:
```bash
uvicorn backend.main:app --reload
```

2. Open the frontend/select_salon.html file in a web browser

## Usage

1. Click the "Start Voice Assistant" button
2. Wait for the "Hello! How can I help you today?" prompt
3. Speak your request (e.g., "I want to book an appointment")
4. Follow the assistant's prompts to provide:
   - Your name
   - Desired service
   - Preferred salon
   - Appointment time

The assistant will check availability and confirm your booking or suggest alternative time slots if necessary.

## Sample Data

The system comes pre-loaded with two sample salons:

1. Elegant Cuts
   - Services: Haircut, Color Treatment
   - Hours: 9:00 AM - 6:00 PM

2. Style Studio
   - Services: Manicure, Pedicure
   - Hours: 10:00 AM - 7:00 PM

## Troubleshooting

- Make sure your microphone is properly connected and has necessary permissions
- Check that MongoDB is running on the default port (27017)
- Ensure all Python dependencies are installed correctly
- If you encounter any issues with speech recognition, try speaking clearly and in a quiet environment