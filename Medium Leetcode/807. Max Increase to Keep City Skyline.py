def maxIncreaseKeepingSkyline(grid: list[list[int]]) -> int:
    n = len(grid)
    # arr = [[]*n]*n
    # print(arr)
    columns = list(zip(*grid))
    maxrow = [max(row) for row in grid]
    maxcolumn = [max(row) for row in columns]
    res = 0
    for row in range(n):
        for col in range(n):
            if (grid[row][col] != maxcolumn[col] and grid[row][col] != maxrow[row]):
                mini = min(maxcolumn[col], maxrow[row])
                res += mini - grid[row][col]

    print(res)
    # print(arr)
            # grid[row][col] == row.max()  
    
    
    print(columns)
        



maxIncreaseKeepingSkyline(grid = [[3,0,8,4],[2,4,5,7],[9,2,6,3],[0,3,1,0]])