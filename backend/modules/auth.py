from flask import request, jsonify
from flask_bcrypt import Bcrypt
from pymongo import MongoClient

bcrypt = Bcrypt()
client = MongoClient("mongodb://localhost:27017/")
db = client["salonova"]
users = db["users"]

def register_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if users.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    users.insert_one({"username": username, "password": hashed_pw})
    return jsonify({"message": "User registered successfully"}), 201

def login_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = users.find_one({"username": username})
    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful"}), 200
