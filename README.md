# 💇‍♀️ Salonova: Talk2Book – Voice Assistant for Salon Booking 🎙️

An **AI-powered voice assistant** that makes salon appointment booking hands-free and hassle-free! Built as a part of **Holboxathon**, this smart system uses **speech recognition** to interact with users, check availability, and suggest the next possible time slot — all in real-time.

---

## 🌟 Features

- 🎤 **Voice-based Interaction** – Book appointments just by speaking
- 📅 **Real-time Slot Checking** – No more guessing when your stylist is free
- 🤖 **Automatic Slot Suggestion** – Smart fallback when your preferred time is unavailable
- 🧠 **MongoDB Data Integration** – All bookings are safely stored
- 🏢 **Multi-Salon Support** – Choose from different salons and services

---

## 👥 Team

This project was created by a team Code Crafters as a part of **Holboxathon**:
Contributors:
- Vidhi Ladani
- Palak Kanjiya
- Dhyey Shah
- Parth Changera


---

## 🛠️ Prerequisites

- 🐍 Python 3.8+
- 🍃 MongoDB (running on `localhost:27017`)
- 🧩 Node.js (for frontend execution)
- 🎙️ Microphone (for voice input)

---

## ⚙️Installation

1. Install MongoDB and make sure it's running on localhost:27017

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database with sample data:
```bash
python backend/init_db.py
```

## 🚀Running the Application

1. Start the backend server:
```bash
uvicorn backend.main:app --reload
```

2. Open the frontend/select_salon.html file in a web browser

## 🎯Usage

1. Click the "Start Voice Assistant" button
2. Wait for the "Hello! How can I help you today?" prompt
3. Speak your request (e.g., "I want to book an appointment")
4. Follow the assistant's prompts to provide:
   - Your name
   - Desired service
   - Preferred salon
   - Appointment time

The assistant will check availability and confirm your booking or suggest alternative time slots if necessary.

## 🧪Sample Data

The system comes pre-loaded with two sample salons:

1. Elegant Cuts
   - Services: Haircut, Color Treatment
   - Hours: 9:00 AM - 6:00 PM

2. Style Studio
   - Services: Manicure, Pedicure
   - Hours: 10:00 AM - 7:00 PM

---

## 🎬 Demo Video

Watch the demo of **Salonova: Talk2Book** in action on YouTube:

click here: [Demo Video on YouTube](https://youtu.be/jTRF2rQfHMs?feature=shared)

## 🛠️Troubleshooting

- ✅Make sure your microphone is properly connected and has necessary permissions
- ✅Check that MongoDB is running on the default port (27017)
- ✅Ensure all Python dependencies are installed correctly
- ✅If you encounter any issues with speech recognition, try speaking clearly and in a quiet environment

---

## 🙌 Final Thoughts

**Salonova: Talk2Book** was built with the vision of making salon appointment booking more accessible, hands-free, and intelligent. By combining voice technology with real-time scheduling and database integration, we’ve created a system that can be scaled across multiple salons and services.

This project was a great learning experience in full-stack development, AI integration, and teamwork — and we’re proud to present it as a part of **Holboxathon**.

If you like our work, feel free to ⭐ star the repo, suggest features, or contribute!

---

> _"Speak to book, and let the assistant do the rest."_ 🎙️💇‍♂️💇‍♀️

---

Made with ❤️ by Team Code Crafters
