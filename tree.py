class TreeNode:
    def __init__(self, data):
        self.data = data
        self.children = []

root = TreeNode("Class")

def add_subject(subject):
    root.children.append(TreeNode(subject))

def display_tree(node, level=0):
    print(" " * level * 4 + node.data)
    for child in node.children:
        display_tree(child, level + 1)
