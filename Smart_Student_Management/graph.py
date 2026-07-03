friend_graph = {}

def add_friend(student1, student2):
    friend_graph.setdefault(student1, []).append(student2)
    friend_graph.setdefault(student2, []).append(student1)

def show_graph():
    print("\n--- Student Friendship Graph ---")
    for student, friends in friend_graph.items():
        print(student, "->", friends)
