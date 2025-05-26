from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import asyncio
from datetime import datetime, timedelta
import pytz

async def init_db():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.salon_db

    try:
        # Clear existing collections
        await db.salons.delete_many({})
        await db.services.delete_many({})
        await db.appointments.delete_many({})

        # Insert sample salons with proper business hours
        salons = [
            {
                "name": "Elegant Cuts",
                "address": "123 Main St",
                "phone": "555-0101",
                "email": "elegant@cuts.com",
                "opening_time": "09:00",  # 9 AM
                "closing_time": "17:00",  # 5 PM
                "services": []
            },
            {
                "name": "Style Studio",
                "address": "456 Oak Ave",
                "phone": "555-0102",
                "email": "style@studio.com",
                "opening_time": "10:00",  # 10 AM
                "closing_time": "18:00",  # 6 PM
                "services": []
            }
        ]

        salon_ids = []
        for salon in salons:
            result = await db.salons.insert_one(salon)
            salon_ids.append(result.inserted_id)
            print(f"Created salon: {salon['name']} with ID: {result.inserted_id}")

        # Insert sample services with reasonable durations
        services = [
            {
                "name": "Haircut",
                "description": "Basic haircut and styling",
                "duration": 30,  # 30 minutes
                "price": 30.00,
                "salon_id": str(salon_ids[0])
            },
            {
                "name": "Color Treatment",
                "description": "Hair coloring service",
                "duration": 90,  # 90 minutes
                "price": 100.00,
                "salon_id": str(salon_ids[0])
            },
            {
                "name": "Manicure",
                "description": "Basic manicure service",
                "duration": 45,  # 45 minutes
                "price": 35.00,
                "salon_id": str(salon_ids[1])
            },
            {
                "name": "Pedicure",
                "description": "Basic pedicure service",
                "duration": 60,  # 60 minutes
                "price": 45.00,
                "salon_id": str(salon_ids[1])
            }
        ]

        for service in services:
            result = await db.services.insert_one(service)
            print(f"Created service: {service['name']} with ID: {result.inserted_id}")
            # Update salon's services list
            await db.salons.update_one(
                {"_id": ObjectId(service["salon_id"])},
                {"$push": {"services": str(result.inserted_id)}}
            )

        print("Database initialized with sample data!")
        
        # Verify the data
        salons_count = await db.salons.count_documents({})
        services_count = await db.services.count_documents({})
        appointments_count = await db.appointments.count_documents({})
        print(f"Verification: Found {salons_count} salons, {services_count} services, and {appointments_count} appointments")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(init_db()) 