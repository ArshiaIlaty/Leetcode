from collections import defaultdict
import heapq

def networkDelayTime(times: list[list[int]], n: int, k: int) -> int:
    # max size of heap can be up to V squared
    # every heap operation in worst case is E * log v
    edges = defaultdict(list) # empty list, Adjacency list creation
    for u,v,w in times:
        edges[u].append((v,w))
        print(edges)
        print('--------------------------------')
    # pq = PriorityQueue()
    # (cost,node)
    minheap = [(0,k)]
    # heapq.heapify()
    visited = set()
    t = 0
    while minheap:
        cost, node = heapq.heappop(minheap) # my mistake: minheap.pop()
        print(cost, node)
        print('--------------------------------')
        if node in visited:
            continue
        visited.add(node)
        print(visited)
        t = max(t, cost)
        print(t)
        for neighbors, costs in edges[node]:
            print("neighbors, costs")
            print(neighbors, costs)
            print('--------------------------------')
            if neighbors not in visited:
                heapq.heappush(minheap, (cost + costs, neighbors))
                # visited.add(neighbors)
                print(minheap)
                print('--------------------------------')
    return t if len(visited) == n else -1

print(networkDelayTime([[2,1,1],[2,3,1],[3,4,1]], 4, 2))
print('New--------------------------------')
print(networkDelayTime([[1,2,1],[2,3,2],[1,3,4]], 3, 1))