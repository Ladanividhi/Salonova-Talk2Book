from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
import os
import pytz
from datetime import datetime, timedelta
from models import Salon, Service, Appointment, BookingRequest
from passlib.context import CryptContext
from pydantic import BaseModel
from bson import ObjectId

# Setup paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FRONTEND_DIR = os.path.join(ROOT_DIR, 'frontend')

# FastAPI app
app = FastAPI()

# Enable CORS
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mount static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# MongoDB connection
MONGO_URL = "mongodb://localhost:27017"
client = None
db = None
in_memory_db = {
    "appointments": [],
    "salons": [],
    "services": []
}

# IST offset from UTC is +5:30
IST_OFFSET = timedelta(hours=5, minutes=30)

def convert_to_ist(dt):
    """Convert any datetime to IST using UTC+5:30 formula"""
    if dt.tzinfo is None:
        # If no timezone info, assume UTC
        dt = dt.replace(tzinfo=pytz.UTC)
    # Convert to UTC first
    utc_time = dt.astimezone(pytz.UTC)
    # Add 5:30 hours to get IST
    ist_time = utc_time + IST_OFFSET
    return ist_time

def get_current_ist_time():
    """Get current time in IST using UTC+5:30 formula"""
    current_utc = datetime.now(pytz.UTC)
    return current_utc + IST_OFFSET

def get_db():
    global client, db
    if db is not None:
        return db
    try:
        print("Attempting to connect to MongoDB...")
        client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        db = client.salon_db
        print("Successfully connected to MongoDB")
        return db
    except Exception as e:
        print(f"Warning: MongoDB connection failed: {e}")
        return None

# User models
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class BookingRequest(BaseModel):
    name: str
    salon: str
    service: str
    dateTime: str

class NextSlotConfirmation(BaseModel):
    confirm: bool
    original_request: BookingRequest
    next_slot: str

@app.on_event("startup")
async def startup_db_client():
    try:
        db = get_db()
        if db is None:
            print("Warning: Using in-memory storage as MongoDB is not available")
            # Initialize in-memory data
            in_memory_db["salons"] = [{
                "_id": "1",
                "name": "Elegant Cuts",
                "address": "123 Main St",
                "phone": "555-0101",
                "email": "elegant@cuts.com",
                "opening_time": "09:00",
                "closing_time": "17:00",
                "services": ["1"]
            }]
            in_memory_db["services"] = [{
                "_id": "1",
                "name": "Haircut",
                "description": "Basic haircut and styling",
                "duration": 30,
                "price": 30.00,
                "salon_id": "1"
            }]
            return

        # If MongoDB is available, create indexes and initialize data
        await db.appointments.create_index([("salon_id", 1), ("appointment_time", 1)])
        await db.appointments.create_index([("status", 1)])
        print("Connected to MongoDB and created indexes!")
        
        if await db.salons.count_documents({}) == 0:
            # Add sample salon
            salon = {
                "name": "Elegant Cuts",
                "address": "123 Main St",
                "phone": "555-0101",
                "email": "elegant@cuts.com",
                "opening_time": "09:00",
                "closing_time": "17:00",
                "services": []
            }
            result = await db.salons.insert_one(salon)
            salon_id = str(result.inserted_id)
            
            # Add sample service
            service = {
                "name": "Haircut",
                "description": "Basic haircut and styling",
                "duration": 30,
                "price": 30.00,
                "salon_id": salon_id
            }
            service_result = await db.services.insert_one(service)
            
            # Update salon's services
            await db.salons.update_one(
                {"_id": result.inserted_id},
                {"$push": {"services": str(service_result.inserted_id)}}
            )
            print("Initialized database with sample data!")
    except Exception as e:
        print(f"Error in startup: {e}")
        print("Warning: Using in-memory storage as MongoDB is not available")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.get("/")
async def read_root():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))
    
@app.get("/login.html")
async def read_root():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/index.html")
async def get_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/signup.html")
async def get_signup():
    return FileResponse(os.path.join(FRONTEND_DIR, "signup.html"))

@app.get("/select_salon.html")
async def get_select_salon():
    return FileResponse(os.path.join(FRONTEND_DIR, "select_salon.html"))

@app.get("/help.html")
async def get_help():
    return FileResponse(os.path.join(FRONTEND_DIR, "help.html"))

@app.get("/contact.html")
async def get_contact():
    return FileResponse(os.path.join(FRONTEND_DIR, "contact.html"))

@app.post("/api/signup")
async def signup(user: UserCreate):
    try:
        # Check if username already exists
        existing_user = await db.users.find_one({"username": user.username})
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Hash the password
        hashed_password = pwd_context.hash(user.password)

        # Create new user
        user_dict = {
            "username": user.username,
            "password": hashed_password
        }
        
        result = await db.users.insert_one(user_dict)
        if result.inserted_id:
            return {"message": "User registered successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/login")
async def login(user: UserLogin):
    try:
        # Find user
        db_user = await db.users.find_one({"username": user.username})
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Verify password
        if not pwd_context.verify(user.password, db_user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {"message": "Login successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/check-availability")
async def check_availability(booking_request: BookingRequest):
    try:
        print("\n=== TIME DEBUGGING ===")
        print(f"1. Raw booking request time (UTC): {booking_request.dateTime}")
        
        # Find the salon
        salon = await db.salons.find_one({"name": booking_request.salon})
        if not salon:
            raise HTTPException(status_code=404, detail="Salon not found")

        # Find the service
        service = await db.services.find_one({
            "name": booking_request.service,
            "salon_id": str(salon["_id"])
        })
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

        # Parse the requested datetime and convert to IST
        try:
            # Parse the UTC time first
            date_str = booking_request.dateTime.replace('Z', '')
            utc_time = datetime.fromisoformat(date_str)
            print(f"2. Parsed UTC time: {utc_time.strftime('%Y-%m-%d %I:%M %p')}")
            
            # Convert to IST by adding 5:30 hours
            ist_offset = timedelta(hours=5, minutes=30)
            requested_time_ist = utc_time + ist_offset
            requested_time_ist = requested_time_ist.replace(second=0, microsecond=0)
            print(f"3. Converted to IST (+5:30): {requested_time_ist.strftime('%Y-%m-%d %I:%M %p')}")
            
            # Check if time is in the past
            current_time = datetime.now().replace(second=0, microsecond=0)
            ist_current_time = current_time + ist_offset
            print(f"4. Current time (IST): {ist_current_time.strftime('%Y-%m-%d %I:%M %p')}")

            if requested_time_ist.date() < ist_current_time.date():
                next_slot = ist_current_time + timedelta(days=1)
                next_slot = next_slot.replace(hour=9, minute=0)  # Next day 9 AM
                return {
                    "available": False,
                    "requested_time": requested_time_ist.strftime("%Y-%m-%d %H:%M IST"),
                    "message": "Cannot book appointments in the past",
                    "nextAvailable": next_slot.strftime("%Y-%m-%d %H:%M IST"),
                    "suggestNext": True
                }
            elif requested_time_ist.date() == ist_current_time.date() and requested_time_ist.time() < ist_current_time.time():
                next_slot = ist_current_time + timedelta(hours=1)
                if next_slot.time() > datetime.strptime(salon["closing_time"], "%H:%M").time():
                    next_slot = (ist_current_time + timedelta(days=1)).replace(hour=9, minute=0)  # Next day 9 AM
                return {
                    "available": False,
                    "requested_time": requested_time_ist.strftime("%Y-%m-%d %H:%M IST"),
                    "message": "Cannot book appointments in the past",
                    "nextAvailable": next_slot.strftime("%Y-%m-%d %H:%M IST"),
                    "suggestNext": True
                }

        except ValueError as e:
            print(f"DateTime parsing error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")

        # Check if the requested time is within salon hours
        salon_opening = datetime.strptime(salon["opening_time"], "%H:%M").time()
        salon_closing = datetime.strptime(salon["closing_time"], "%H:%M").time()
        requested_time_only = requested_time_ist.time()

        print(f"5. Checking against salon hours:")
        print(f"   - Salon hours: {salon_opening} - {salon_closing}")
        print(f"   - Requested time (IST): {requested_time_only}")

        if not (salon_opening <= requested_time_only <= salon_closing):
            # Find next available slot starting from tomorrow if outside business hours
            next_day = requested_time_ist.date() + timedelta(days=1)
            next_slot = datetime.combine(next_day, salon_opening)
            return {
                "available": False,
                "requested_time": requested_time_ist.strftime("%Y-%m-%d %H:%M IST"),
                "message": f"Requested time {requested_time_only} is outside salon hours ({salon_opening} - {salon_closing})",
                "nextAvailable": next_slot.strftime("%Y-%m-%d %H:%M IST"),
                "suggestNext": True
            }

        # Calculate appointment end time
        service_duration = service.get("duration", 30)  # default 30 minutes if not specified
        end_time_ist = requested_time_ist + timedelta(minutes=service_duration)
        print(f"6. Appointment end time (IST): {end_time_ist.strftime('%Y-%m-%d %I:%M %p')}")

        # Check if end time is within business hours
        if end_time_ist.time() > salon_closing:
            next_day = requested_time_ist.date() + timedelta(days=1)
            next_slot = datetime.combine(next_day, salon_opening)
            return {
                "available": False,
                "requested_time": requested_time_ist.strftime("%Y-%m-%d %H:%M IST"),
                "message": "Appointment would end after business hours",
                "nextAvailable": next_slot.strftime("%Y-%m-%d %H:%M IST"),
                "suggestNext": True
            }

        # Check for conflicting appointments - all times in database are in IST
        existing_appointments = await db.appointments.find({
            "salon_id": str(salon["_id"]),
            "$or": [
                {
                    "appointment_time": {"$lt": end_time_ist},
                    "end_time": {"$gt": requested_time_ist}
                },
                {
                    "appointment_time": requested_time_ist,
                    "status": "scheduled"
                }
            ],
            "status": "scheduled"
        }).to_list(length=None)

        if existing_appointments:
            # Find next available slot
            next_slot = requested_time_ist
            found_slot = False
            max_attempts = 14  # Check up to 14 slots ahead
            attempts = 0

            while not found_slot and attempts < max_attempts:
                next_slot = next_slot + timedelta(minutes=30)
                if next_slot.time() > salon_closing:
                    # Move to next day's opening time
                    next_day = next_slot.date() + timedelta(days=1)
                    next_slot = datetime.combine(next_day, salon_opening)
                    continue

                if next_slot.time() < salon_opening:
                    # Move to same day's opening time
                    next_slot = datetime.combine(next_slot.date(), salon_opening)
                    continue

                # Check if this slot is available
                slot_end = next_slot + timedelta(minutes=service_duration)
                conflicts = await db.appointments.find_one({
                    "salon_id": str(salon["_id"]),
                    "$or": [
                        {
                            "appointment_time": {"$lt": slot_end},
                            "end_time": {"$gt": next_slot}
                        },
                        {
                            "appointment_time": next_slot,
                            "status": "scheduled"
                        }
                    ],
                    "status": "scheduled"
                })

                if not conflicts:
                    found_slot = True
                    break

                attempts += 1

            return {
                "available": False,
                "requested_time": requested_time_ist.strftime("%Y-%m-%d %H:%M IST"),
                "message": "Time slot not available",
                "nextAvailable": next_slot.strftime("%Y-%m-%d %H:%M IST") if found_slot else None,
                "suggestNext": True
            }

        print("7. Slot is available!")
        return {
            "available": True,
            "requested_time": requested_time_ist.strftime("%Y-%m-%d %H:%M IST"),
            "salon_id": str(salon["_id"]),
            "service_id": str(service["_id"]),
            "appointment_time": requested_time_ist.strftime("%Y-%m-%d %H:%M IST"),
            "end_time": end_time_ist.strftime("%Y-%m-%d %H:%M IST")
        }

    except Exception as e:
        print(f"Error in check_availability: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/book-appointment")
async def book_appointment(booking_request: BookingRequest):
    try:
        print("\n=== APPOINTMENT BOOKING DEBUG ===")
        print(f"1. Initial booking request time (UTC): {booking_request.dateTime}")
        
        # Convert requested time to IST
        ist_time = datetime.fromisoformat(booking_request.dateTime.replace('Z', '')) + timedelta(hours=5, minutes=30)
        end_time = ist_time + timedelta(minutes=30)  # Assuming 30 minutes duration

        print(f"2. Checking slot {ist_time.strftime('%Y-%m-%d %H:%M IST')} - {end_time.strftime('%Y-%m-%d %H:%M IST')}")

        # Check for any overlapping appointments
        existing_appointments = await db.appointments.find({
            "salon": booking_request.salon,
            "$or": [
                # Case 1: New appointment starts during an existing appointment
                {
                    "appointment_time": {"$lte": ist_time},
                    "end_time": {"$gt": ist_time}
                },
                # Case 2: New appointment ends during an existing appointment
                {
                    "appointment_time": {"$lt": end_time},
                    "end_time": {"$gte": end_time}
                },
                # Case 3: New appointment completely contains an existing appointment
                {
                    "appointment_time": {"$gte": ist_time},
                    "end_time": {"$lte": end_time}
                }
            ],
            "status": "scheduled"
        }).to_list(length=None)

        if existing_appointments:
            print(f"3. Found conflicting appointments: {len(existing_appointments)}")
            # Find the next available slot after all conflicting appointments
            next_possible_time = max(appt["end_time"] for appt in existing_appointments)
            next_slot = next_possible_time
            
            # Format next slot time for display
            next_slot_str = next_slot.strftime("%Y-%m-%d %H:%M IST")
            
            return {
                "status": "slot_unavailable",
                "message": f"The requested slot is not available. Would you like to book the next available slot at {next_slot_str}?",
                "next_available_slot": next_slot_str
            }

        print("3. No conflicting appointments found")

        # Create appointment document
        appointment_doc = {
            "customer_name": booking_request.name,
            "salon": booking_request.salon,
            "service": booking_request.service,
            "appointment_time": ist_time,
            "end_time": end_time,
            "status": "scheduled",
            "timezone": "IST"
        }

        print("4. Attempting to insert appointment")
        # Try to insert the appointment
        try:
            # Use a unique index to prevent race conditions
            await db.appointments.create_index([
                ("salon", 1),
                ("appointment_time", 1),
                ("status", 1)
            ], unique=True)

            result = await db.appointments.insert_one(appointment_doc)
            
            if result.inserted_id:
                print(f"5. Successfully booked appointment with ID: {result.inserted_id}")
                return {
                    "status": "success",
                    "message": "Appointment booked successfully",
                    "appointment_id": str(result.inserted_id),
                    "appointment_time": ist_time.strftime("%Y-%m-%d %H:%M IST"),
                    "end_time": end_time.strftime("%Y-%m-%d %H:%M IST")
                }
            else:
                print("5. Failed to insert appointment")
                return {
                    "status": "error",
                    "message": "Failed to book appointment"
                }
        except Exception as e:
            print(f"5. Database error: {str(e)}")
            # Check if this was a duplicate key error
            if "duplicate key error" in str(e).lower():
                next_slot = ist_time + timedelta(minutes=30)
                return {
                    "status": "slot_unavailable",
                    "message": f"This slot was just taken. Would you like to book the next available slot at {next_slot.strftime('%Y-%m-%d %H:%M IST')}?",
                    "next_available_slot": next_slot.strftime("%Y-%m-%d %H:%M IST")
                }
            return {
                "status": "error",
                "message": f"Error booking appointment: {str(e)}"
            }

    except Exception as e:
        print(f"Error in book_appointment: {str(e)}")
        return {
            "status": "error",
            "message": f"Error processing request: {str(e)}"
        }

@app.post("/api/confirm-next-slot")
async def confirm_next_slot(booking_request: BookingRequest, next_slot: str):
    try:
        # Convert the next slot string to datetime
        next_slot_time = datetime.strptime(next_slot, "%Y-%m-%d %H:%M IST")
        end_time = next_slot_time + timedelta(minutes=30)  # Assuming 30 minutes duration

        print(f"1. Checking next slot {next_slot_time.strftime('%Y-%m-%d %H:%M IST')} - {end_time.strftime('%Y-%m-%d %H:%M IST')}")

        # Check for any overlapping appointments
        existing_appointments = await db.appointments.find({
            "salon": booking_request.salon,
            "$or": [
                # Case 1: New appointment starts during an existing appointment
                {
                    "appointment_time": {"$lte": next_slot_time},
                    "end_time": {"$gt": next_slot_time}
                },
                # Case 2: New appointment ends during an existing appointment
                {
                    "appointment_time": {"$lt": end_time},
                    "end_time": {"$gte": end_time}
                },
                # Case 3: New appointment completely contains an existing appointment
                {
                    "appointment_time": {"$gte": next_slot_time},
                    "end_time": {"$lte": end_time}
                }
            ],
            "status": "scheduled"
        }).to_list(length=None)

        if existing_appointments:
            print(f"2. Found conflicting appointments: {len(existing_appointments)}")
            # Find the next available slot after all conflicting appointments
            next_possible_time = max(appt["end_time"] for appt in existing_appointments)
            next_available = next_possible_time
            return {
                "status": "slot_unavailable",
                "message": f"Sorry, that slot was just taken. Would you like to book the next available slot at {next_available.strftime('%Y-%m-%d %H:%M IST')}?",
                "next_available_slot": next_available.strftime("%Y-%m-%d %H:%M IST")
            }

        print("2. No conflicting appointments found")

        # Create appointment document
        appointment_doc = {
            "customer_name": booking_request.name,
            "salon": booking_request.salon,
            "service": booking_request.service,
            "appointment_time": next_slot_time,
            "end_time": end_time,
            "status": "scheduled",
            "timezone": "IST"
        }

        print("3. Attempting to insert appointment")
        # Try to insert the appointment
        try:
            # Use a unique index to prevent race conditions
            await db.appointments.create_index([
                ("salon", 1),
                ("appointment_time", 1),
                ("status", 1)
            ], unique=True)

            result = await db.appointments.insert_one(appointment_doc)
            
            if result.inserted_id:
                print(f"4. Successfully booked appointment with ID: {result.inserted_id}")
                return {
                    "status": "success",
                    "message": "Appointment booked successfully",
                    "appointment_id": str(result.inserted_id),
                    "appointment_time": next_slot_time.strftime("%Y-%m-%d %H:%M IST"),
                    "end_time": end_time.strftime("%Y-%m-%d %H:%M IST")
                }
            else:
                print("4. Failed to insert appointment")
                return {
                    "status": "error",
                    "message": "Failed to book appointment"
                }
        except Exception as e:
            print(f"4. Database error: {str(e)}")
            # Check if this was a duplicate key error
            if "duplicate key error" in str(e).lower():
                next_available = next_slot_time + timedelta(minutes=30)
                return {
                    "status": "slot_unavailable",
                    "message": f"This slot was just taken. Would you like to book the next available slot at {next_available.strftime('%Y-%m-%d %H:%M IST')}?",
                    "next_available_slot": next_available.strftime("%Y-%m-%d %H:%M IST")
                }
            return {
                "status": "error",
                "message": f"Error booking appointment: {str(e)}"
            }

    except Exception as e:
        print(f"Error in confirm_next_slot: {str(e)}")
        return {
            "status": "error",
            "message": f"Error processing request: {str(e)}"
        }

@app.get("/api/check-db-connection")
async def check_db_connection():
    try:
        print("Checking database connection...")
        db = get_db()
        if db is None:
            return {"status": "error", "message": "Could not connect to database"}
            
        # Try to ping the database
        await db.command("ping")
        
        # Get collection statistics
        stats = {
            "users": await db.users.count_documents({}),
            "appointments": await db.appointments.count_documents({}),
            "salons": await db.salons.count_documents({}),
            "services": await db.services.count_documents({})
        }
        
        return {
            "status": "connected",
            "message": "Successfully connected to MongoDB",
            "collections": stats
        }
    except Exception as e:
        print(f"Error checking database connection: {e}")
        return {"status": "error", "message": str(e)}

async def find_next_available_slot(salon: dict, service: dict, after_time: datetime = None):
    try:
        print(f"\nDebug: Starting slot search")
        print(f"Debug: Salon hours: {salon['opening_time']} - {salon['closing_time']}")
        print(f"Debug: Service duration: {service['duration']} minutes")
        
        # Initialize the search start time
        if not after_time:
            after_time = datetime.now(pytz.UTC)
        elif not after_time.tzinfo:
            after_time = pytz.UTC.localize(after_time)
        
        print(f"Debug: Search start time: {after_time}")

        # Get salon hours
        opening_time = datetime.strptime(salon["opening_time"], "%H:%M").time()
        closing_time = datetime.strptime(salon["closing_time"], "%H:%M").time()
        
        # Adjust start time to be within business hours
        current_time = after_time.replace(second=0, microsecond=0)
        if current_time.time() < opening_time:
            # If before opening, set to today's opening time
            current_time = current_time.replace(
                hour=opening_time.hour,
                minute=opening_time.minute
            )
        elif current_time.time() > closing_time:
            # If after closing, set to next day's opening time
            current_time = (current_time + timedelta(days=1)).replace(
                hour=opening_time.hour,
                minute=opening_time.minute,
                second=0,
                microsecond=0
            )
        
        print(f"Debug: Adjusted start time: {current_time}")

        # Set end date for search (7 days from start)
        end_date = after_time + timedelta(days=7)
        print(f"Debug: Search end date: {end_date}")

        # Get all appointments for the next 7 days
        appointments = await db.appointments.find({
            "salon_id": str(salon["_id"]),
            "appointment_time": {
                "$gte": current_time,
                "$lte": end_date
            },
            "status": "scheduled"
        }).sort("appointment_time", 1).to_list(length=None)
        
        print(f"Debug: Found {len(appointments)} existing appointments in date range")

        # Service duration in minutes
        service_duration = timedelta(minutes=service["duration"])

        # Check each 15-minute slot for the next 7 days
        slots_checked = 0
        while current_time <= end_date:
            slots_checked += 1
            # Skip if outside business hours
            if current_time.time() < opening_time:
                # Move to today's opening time
                current_time = current_time.replace(
                    hour=opening_time.hour,
                    minute=opening_time.minute
                )
                print(f"Debug: Adjusted to opening time: {current_time}")
            elif current_time.time() > closing_time:
                # Move to next day's opening time
                current_time = (current_time + timedelta(days=1)).replace(
                    hour=opening_time.hour,
                    minute=opening_time.minute,
                    second=0,
                    microsecond=0
                )
                print(f"Debug: Moved to next day: {current_time}")
                continue

            # Calculate slot end time
            slot_end = current_time + service_duration

            # Skip if slot would end after closing time
            if slot_end.time() > closing_time:
                print(f"Debug: Slot would end after closing time: {slot_end.time()}")
                # Move to next day's opening time
                current_time = (current_time + timedelta(days=1)).replace(
                    hour=opening_time.hour,
                    minute=opening_time.minute,
                    second=0,
                    microsecond=0
                )
                continue

            # Check for conflicts with existing appointments
            has_conflict = False
            for appt in appointments:
                # Check if current slot overlaps with any appointment
                if (current_time < appt["end_time"] and 
                    slot_end > appt["appointment_time"]):
                    has_conflict = True
                    print(f"Debug: Conflict found at {current_time}")
                    # Move time to the end of conflicting appointment
                    current_time = appt["end_time"].replace(second=0, microsecond=0)
                    break

            if not has_conflict:
                print(f"Debug: Found available slot at {current_time}")
                return current_time

            # Move to next 15-minute slot if no valid slot found
            current_time += timedelta(minutes=15)

        print(f"Debug: No available slots found after checking {slots_checked} slots")
        return None

    except Exception as e:
        print(f"Error finding next available slot: {str(e)}")
        return None

@app.get("/api/appointments/{appointment_id}")
async def get_appointment(appointment_id: str):
    try:
        # Find the appointment
        appointment = await db.appointments.find_one({"_id": ObjectId(appointment_id)})
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        # Times are already in IST in the database
        appointment_time = appointment["appointment_time"]
        end_time = appointment["end_time"]

        return {
            "appointment_id": str(appointment["_id"]),
            "customer_name": appointment["customer_name"],
            "appointment_time": appointment_time.strftime("%Y-%m-%d %H:%M IST"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M IST"),
            "status": appointment["status"],
            "timezone": "IST"
        }
    except Exception as e:
        print(f"Error retrieving appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/appointments")
async def get_all_appointments():
    try:
        # Get all appointments
        appointments = await db.appointments.find({}).to_list(length=None)
        
        # Times are already in IST in the database
        formatted_appointments = []
        for appt in appointments:
            appointment_time = appt["appointment_time"]
            end_time = appt["end_time"]

            formatted_appointments.append({
                "appointment_id": str(appt["_id"]),
                "customer_name": appt["customer_name"],
                "appointment_time": appointment_time.strftime("%Y-%m-%d %H:%M IST"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M IST"),
                "status": appt["status"],
                "timezone": "IST"
            })

        return formatted_appointments
    except Exception as e:
        print(f"Error retrieving appointments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)


