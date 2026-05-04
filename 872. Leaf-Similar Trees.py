def leafSimilar(root1: TreeNode, root2: TreeNode) -> bool:
    def getLeaves(root: TreeNode) -> list[int]:
        if not root:
            return []
        if not root.left and not root.right:
            return [root.val]
        return getLeaves(root.left) + getLeaves(root.right)
    return getLeaves(root1) == getLeaves(root2)

print(leafSimilar(root1, root2))
