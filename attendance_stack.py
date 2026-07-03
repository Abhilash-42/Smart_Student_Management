attendance_stack = []

def mark_attendance(student, status):
    attendance_stack.append(student.attendance)
    student.attendance = status

def undo_attendance(student):
    if attendance_stack:
        student.attendance = attendance_stack.pop()
        print("Attendance undo successful")
    else:
        print("No attendance to undo")
