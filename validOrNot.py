# # Definition for a binary tree node.
# # class TreeNode:
# #     def __init__(self, val=0, left=None, right=None):
# #         self.val = val
# #         self.left = left
# #         self.right = right
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right

# class Solution:
#     def validOrNot(self, root1: Optional[TreeNode], root2: Optional[TreeNode]) -> bool:
#         def leaves(root):
#             leaves = []
#             print(leaves)
#             def dfs(node):
#                 if not node: return
#                 if node.left is None and node.right is None:
#                     leaves.append(node.val)
#                     print(leaves)
#                     return
#                 dfs(node.left)
#                 dfs(node.right)
#             dfs(root)
#             print(leaves)
#             return leaves
        
#         return leaves(root1) == leaves(root2)

# # an object of the class
# print(Solution().validOrNot(root1, root2))


from typing import Optional

# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def validOrNot(self, root1: Optional[TreeNode], root2: Optional[TreeNode]) -> bool:
        def leaves(root, label):
            leaves = []
            print(f"\n=== Collecting leaves for {label} ===")

            def dfs(node, depth=0):
                indent = "  " * depth
                if not node:
                    print(f"{indent}Reached None, backtrack")
                    return

                print(f"{indent}Visiting node with value: {node.val}")

                if node.left is None and node.right is None:
                    leaves.append(node.val)
                    print(f"{indent}Leaf found! leaves so far: {leaves}")
                    return

                print(f"{indent}Go left from {node.val}")
                dfs(node.left, depth + 1)

                print(f"{indent}Go right from {node.val}")
                dfs(node.right, depth + 1)

            dfs(root)
            print(f"All leaves for {label}: {leaves}\n")
            return leaves

        left_leaves = leaves(root1, "root1")
        right_leaves = leaves(root2, "root2")
        print(f"Comparison result: {left_leaves} == {right_leaves} ? {left_leaves == right_leaves}")
        return left_leaves == right_leaves
    

root1 = TreeNode(3, TreeNode(5, TreeNode(6), TreeNode(2, TreeNode(7), TreeNode(4))), TreeNode(1, TreeNode(9), TreeNode(8)))
root2 = TreeNode(3, TreeNode(5, TreeNode(6), TreeNode(7, TreeNode(4), TreeNode(2))), TreeNode(1, TreeNode(9), TreeNode(8)))

from collections import deque

def build_tree(values):
    """Builds a binary tree from a level-order list with None for missing nodes."""
    if not values or values[0] is None:
        return None

    root = TreeNode(values[0])
    queue = deque([root])
    i = 1

    while queue and i < len(values):
        node = queue.popleft()
        if i < len(values) and values[i] is not None:
            node.left = TreeNode(values[i])
            queue.append(node.left)
        i += 1
        if i < len(values) and values[i] is not None:
            node.right = TreeNode(values[i])
            queue.append(node.right)
        i += 1

    return root

# Example 1
root1 = build_tree([3,5,1,6,2,9,8,None,None,7,4])
root2 = build_tree([3,5,1,6,7,4,2,None,None,None,None,None,None,9,8])
print(Solution().validOrNot(root1, root2))  # True

# Example 2
root1 = build_tree([1,2,3])
root2 = build_tree([1,3,2])
print(Solution().validOrNot(root1, root2))  # False

# Example 3
root1 = build_tree([1])
root2 = build_tree([1,None,2])
print(Solution().validOrNot(root1, root2))  # False

# Example 4
root1 = build_tree([1,2,None,3,None,4])
root2 = build_tree([1,None,2,None,3,None,4])
print(Solution().validOrNot(root1, root2))  # True