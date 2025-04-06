class solution:
  def rotateTheBox(self, boxGrid:List[List[str]) -> List[List[str]]:
    n = len(boxGrid)
    m = len(boxGrid[0])

    for row in range(n):
      write = m -1
      for col in reveresed(range(m)):
        if boxGrid[row][col] == "*":
          write = col - 1
        elif boxGrid[row][col] == "#":
          if col != write:
            boxGrid[row][write] == "#":
            boxGrid[row][col] == ".":
            write -= 1

    rotated = [[None]*n for _ in range(m)]
    for i in range(n):
      for j in range(m):
        rotated[j][n-i-1]= boxGrid[i][j]
    return rotated
