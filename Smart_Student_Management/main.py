from student import Student
from database import insert_student, get_all_students
from attendance_stack import mark_attendance, undo_attendance
from graph import add_friend, show_graph
from tree import add_subject, display_tree, root

students = []

add_subject("Maths")
add_subject("Python")
add_subject("Data Structures")

while True:
    print("\n1. Add Student")
    print("2. Mark Attendance")
    print("3. Undo Attendance")
    print("4. View Students")
    print("5. Student Friendship Graph")
    print("6. Academic Tree")
    print("7. Exit")

    choice = input("Enter choice: ")

    if choice == "1":
        name = input("Enter name: ")
        roll = int(input("Enter roll number: "))
        marks = list(map(int, input("Enter marks separated by space: ").split()))
        s = Student(name, roll, marks)
        students.append(s)
        insert_student(s)
        print("Student added successfully")

    elif choice == "2":
        roll = int(input("Enter roll number: "))
        for s in students:
            if s.roll == roll:
                mark_attendance(s, "Present")

    elif choice == "3":
        roll = int(input("Enter roll number: "))
        for s in students:
            if s.roll == roll:
                undo_attendance(s)

    elif choice == "4":
        for s in students:
            s.display()

    elif choice == "5":
        if len(students) >= 2:
            add_friend(students[0].name, students[1].name)
            show_graph()
        else:
            print("Add more students")

    elif choice == "6":
        display_tree(root)

    elif choice == "7":
        print("Exiting program...")
        break
