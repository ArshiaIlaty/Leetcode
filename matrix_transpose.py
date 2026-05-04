def transpose_matrix(a: list[list[int|float]]) -> list[list[int|float]]:
    """
    Transpose a 2D matrix by swapping rows and columns.
    
    Args:
        a: A 2D matrix of shape (m, n)
    
    Returns:
        The transposed matrix of shape (n, m)
    """
    # transpose: len(a[0]) * len(a)
    trans = []
    for i in range(len(a[0])):
        mini = []
        print(mini)
        for j in range(len(a)):
            mini.append(a[j][i])
            print(mini)
        trans.append(mini)
        print(trans)
    return trans

print(transpose_matrix([[1, 2], [3, 4], [5, 6]]))


# Pythonic way:
#     def transpose_matrix(a):
#         return [list(row) for row in zip(*a)]