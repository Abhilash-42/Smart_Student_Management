class Student:
    def __init__(self, name, roll, marks):
        self.name = name
        self.roll = roll
        self.marks = marks
        self.total = sum(marks)
        self.percentage = self.calculate_percentage()
        self.grade = self.assign_grade()
        self.attendance = "Not Marked"

    def calculate_percentage(self):
        return self.total / len(self.marks)

    def assign_grade(self):
        if self.percentage >= 75:
            return "A"
        elif self.percentage >= 60:
            return "B"
        elif self.percentage >= 40:
            return "C"
        else:
            return "Fail"

    def display(self):
        print("\n--- Student Details ---")
        print("Name:", self.name)
        print("Roll:", self.roll)
        print("Marks:", self.marks)
        print("Percentage:", self.percentage)
        print("Grade:", self.grade)
        print("Attendance:", self.attendance)
