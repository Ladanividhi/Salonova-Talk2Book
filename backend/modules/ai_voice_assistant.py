import speech_recognition as sr
import pyttsx3

recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    print("🤖 Speaking:", text)
    engine.say(text)
    engine.runAndWait()

def capture_and_process_appointment():
    speak("Hello! How can I help you with booking an appointment today?")
    speak("Hello! How are you?")

    print("📍 Reached the listening loop.")
    while True:
        with sr.Microphone() as source:
            print("🎤 Listening...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            print(f"🧑 You said: {text}")
            text = text.lower()

            if "appointment" in text:
                speak("Sure, I can help you book an appointment. What date and time do you prefer?")
            elif "exit" in text or "quit" in text:
                speak("Goodbye! Have a great day.")
                break
            else:
                speak("I'm still learning. Please ask me about booking an appointment.")
        except sr.UnknownValueError:
            speak("Sorry, I couldn't understand that. Please repeat.")
        except sr.RequestError as e:
            speak("Network error. Please check your internet connection.")
            print(f"Error: {e}")
            break
