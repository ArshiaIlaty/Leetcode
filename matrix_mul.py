def matrixmul(a:list[list[int|float]],
              b:list[list[int|float]])-> list[list[int|float]]:
    """
    Multiply two matrices.
    Args:
        a: A 2D matrix of shape (m, n)
        b: A 2D matrix of shape (n, p)
    Returns:
        The product of the two matrices.
    """
    if len(a) != len(b[0]):
        return -1
    c = []
    for i in range(len(a)):
        s = 0
        mini = []
        print(s)
        print('--------------------------------')
        print(mini)
        print('--------------------------------')
        for j in range(len(b[0])):
            s += a[i][j]*b[j][i]
            print(s)
            print('--------------------------------')
        # need the third for for k
        mini.append(s)
        print(mini)
        print('--------------------------------')
    c.append(mini) 
    print(c)
    print('Done--------------------------------')
    return c


print(matrixmul([[1,2,3],[2,3,4],[5,6,7]],[[3,2,1],[4,3,2],[5,4,3]]))

'''
Pythonic way to multiply two matrices.

def matrixmul(a, b):
    return [[sum(x*y for x, y in zip(row, col)) 
             for col in zip(*b)] 
            for row in a]
'''