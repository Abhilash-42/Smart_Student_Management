from flask import Flask, render_template, request, redirect
from reportlab.pdfgen import canvas
import os
from pymongo import MongoClient

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["student_db"]
collection = db["students"]


# Home Page
@app.route("/")
def home():

    students = list(collection.find())

    # remove MongoDB _id field
    for s in students:
        s["_id"] = str(s["_id"])

    return render_template("home.html", students=students)


# Add Student
@app.route("/add", methods=["POST"])
def add_student():

    name = request.form["name"]
    roll = int(request.form["roll"])

    m1 = int(request.form["m1"])
    m2 = int(request.form["m2"])
    m3 = int(request.form["m3"])
    m4 = int(request.form["m4"])
    m5 = int(request.form["m5"])

    marks = [m1, m2, m3, m4, m5]

    total = sum(marks)
    percentage = total / len(marks)

    student = {
        "name": name,
        "roll": roll,
        "marks": marks,
        "percentage": percentage
    }

    collection.insert_one(student)

    return redirect("/")


# Delete Student
@app.route("/delete/<int:roll>")
def delete_student(roll):

    collection.delete_one({"roll": roll})

    return redirect("/")


# Generate PDF Report
@app.route("/report/<int:roll>")
def generate_report(roll):

    student = collection.find_one({"roll": roll})

    filename = f"report_{roll}.pdf"

    c = canvas.Canvas(filename)

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 800, "Student Academic Report")

    # Student info
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f"Name: {student['name']}")
    c.drawString(100, 730, f"Roll Number: {student['roll']}")

    # Subject marks
    subjects = ["Maths", "Physics", "Chemistry", "Computer", "English"]

    y = 700

    for subject, mark in zip(subjects, student["marks"]):
        c.drawString(100, y, f"{subject}: {mark}")
        y -= 25   # spacing between lines

    # Percentage
    c.drawString(100, y-10, f"Percentage: {student['percentage']:.2f}")

    c.save()

    return f"Report Generated Successfully: {filename}"


if __name__ == "__main__":
    app.run(debug=True)