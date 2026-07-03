from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["student_db"]
collection = db["students"]

def insert_student(student):
    collection.insert_one(student.__dict__)

def get_all_students():
    return collection.find()
