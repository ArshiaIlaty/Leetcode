'''
BFS Topological Sort
There are a total of numCourses courses you have to take, labeled from 0 to numCourses - 1. You are given an array prerequisites where prerequisites[i] = [ai, bi] indicates that you must take course bi first if you want to take course ai.

For example, the pair [0, 1], indicates that to take course 0 you have to first take course 1.
Return the ordering of courses you should take to finish all courses. If there are many valid answers, return any of them. If it is impossible to finish all courses, return an empty array.
'''

from collections import deque, defaultdict

def findOrder(numCourses: int, prerequisites: list[list[int]]) -> list[int]:
    adj = defaultdict(list)
    indegree = [0] * numCourses
    
    # 1. Build Graph
    for dest, src in prerequisites:
        adj[src].append(dest)
        indegree[dest] += 1
        print(adj)
        print(indegree)
        print('--------------------------------')
    
    # 2. Init Queue with independent nodes
    queue = deque([i for i in range(numCourses) if indegree[i] == 0])
    res = []
    print(queue)
    print('--------------------------------')
    # 3. Process
    while queue:
        node = queue.popleft()
        res.append(node)
        print(res)
        print('--------------------------------')
        for neighbor in adj[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
        print(queue)
        print('--------------------------------')
    print(res)
    print('--------------------------------')
    return res if len(res) == numCourses else []

# print(findOrder(2, [[1,0]]))
# print(findOrder(2, [[1,0], [0,1]]))
# print(findOrder(3, [[1,0], [2,1]]))
# print(findOrder(3, [[1,0], [2,1], [0,2]]))
# print(findOrder(3, [[1,0], [2,1], [0,2], [1,2]]))
print(findOrder(3, [[1,0], [2,1], [0,2], [1,2], [2,0]]))