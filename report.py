def export_report(student):
    filename = f"{student.roll}_report.txt"

    with open(filename, "w") as file:
        file.write("SMART STUDENT ACADEMIC REPORT\n")
        file.write("===============================\n\n")
        file.write(f"Name       : {student.name}\n")
        file.write(f"Roll No    : {student.roll}\n")
        file.write(f"Marks      : {student.marks}\n")
        file.write(f"Percentage : {round(student.percentage, 2)}\n")
        file.write(f"Grade      : {student.grade}\n")
        file.write(f"Attendance : {student.attendance}\n")

    print(f"\nReport successfully generated → {filename}")
