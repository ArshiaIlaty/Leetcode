def validTree(n: int, edges: list[list[int]]) -> bool:
    # Condition 1: A tree with n nodes must have exactly n-1 edges
    if len(edges) != n - 1:
        return False
    print(n, edges)
    print('--------------------------------')
    # Build Graph
    adj = {i: [] for i in range(n)}
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    print(adj)
    print('--------------------------------')
    # Condition 2: Must be fully connected
    visited = set()
    queue = [0] # Stack for DFS or Queue for BFS
    visited.add(0)
    print(visited)
    print('--------------------------------')
    while queue:
        node = queue.pop(0) 
        for neighbor in adj[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
        print(queue)
        print('--------------------------------')
    # If visited count == n, we reached everyone
    return len(visited) == n

print(validTree(5, [[0,1], [0,2], [0,3], [1,4]]))
print(validTree(5, [[0,1], [1,2], [2,3], [1,3], [1,4]]))
print(validTree(5, [[0,1], [1,2], [2,3], [1,3], [1,4], [4,5]]))
print(validTree(5, [[0,1], [1,2], [2,3], [1,3], [1,4], [4,5], [5,6]]))
print(validTree(5, [[0,1], [1,2], [2,3], [1,3], [1,4], [4,5], [5,6], [6,7]]))
print(validTree(5, [[0,1], [1,2], [2,3], [1,3], [1,4], [4,5], [5,6], [6,7], [7,8]]))
print(validTree(5, [[0,1], [1,2], [2,3], [1,3], [1,4], [4,5], [5,6], [6,7], [7,8], [8,9]]))
print(validTree(5, [[0,1], [1,2], [2,3], [1,3], [1,4], [4,5], [5,6], [6,7], [7,8], [8,9], [9,10]]))
print(validTree(5, [[0,1], [1,2], [2,3], [1,3], [1,4], [4,5], [5,6], [6,7], [7,8], [8,9], [9,10], [10,11]]))
print(validTree(5, [[0,1], [1,2], [2,3], [1,3], [1,4], [4,5], [5,6], [6,7], [7,8], [8,9], [9,10], [10,11], [11,12]]))
print(validTree(5, [[0,1], [1,2], [2,3], [1,3], [1,4], [4,5], [5,6], [6,7], [7,8], [8,9], [9,10], [10,11], [11,12], [12,13]]))
print(validTree(5, [[0,1], [1,2], [2,3], [1,3], [1,4], [4,5], [5,6], [6,7], [7,8], [8,9], [9,10], [10,11], [11,12], [12,13], [13,14]]))