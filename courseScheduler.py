from collections import defaultdict

def canFinish(numCourses: int, prerequisites: list[list[int]]) -> bool:
    graph = defaultdict(list)
    for course, pre in prerequisites:
        graph[course].append(pre)
    print(graph)
    return True

print(canFinish(2, [[1,0]]))
print(canFinish(2, [[1,0], [0,1]]))
print(canFinish(3, [[1,0], [2,1]]))
print(canFinish(3, [[1,0], [2,1], [0,2]]))
print(canFinish(3, [[1,0], [2,1], [0,2], [1,2]]))
print(canFinish(3, [[1,0], [2,1], [0,2], [1,2], [2,0]]))