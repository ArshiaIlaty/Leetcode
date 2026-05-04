from collections import defaultdict, deque

def alienOrder(words: list[str]) -> str:
    # 1. Init Graph and In-Degree
    adj = {c: set() for word in words for c in word}
    
    in_degree = {c: 0 for word in words for c in word}
    print(adj)
    print(in_degree)
    print('--------------------------------')
    # 2. Build the Graph
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i+1]
        min_len = min(len(w1), len(w2))
        print(w1, w2)
        print(min_len)
        print('--------------------------------')
        # Check prefix edge case (e.g., "abc" before "ab" is invalid)
        if len(w1) > len(w2) and w1[:min_len] == w2[:min_len]:
            return ""
        print('--------------------------------')
        for j in range(min_len):
            if w1[j] != w2[j]:
                if w2[j] not in adj[w1[j]]:
                    adj[w1[j]].add(w2[j])
                    in_degree[w2[j]] += 1
                    print(adj)
                    print(in_degree)
                    print('--------------------------------')
                break # Only the first difference matters!
                
    # 3. Topological Sort (BFS)
    queue = deque([c for c in in_degree if in_degree[c] == 0])
    res = []
    print(queue)
    print('--------------------------------')
    while queue:
        char = queue.popleft()
        res.append(char)
        print(res)
        print('--------------------------------')
        for neighbor in adj[char]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
        print(queue)
        print('--------------------------------')
    # If we didn't visit all nodes, there was a cycle
    if len(res) < len(in_degree):
        return ""
        
    return "".join(res)

print(alienOrder(["wrt","wrf","er","ett","rftt"]))
print(alienOrder(["z","x"]))
print(alienOrder(["z","x","z"]))
print(alienOrder(["z","z"]))
print(alienOrder(["z","z","x"]))
print(alienOrder(["z","z","x","z"]))
print(alienOrder(["z","z","x","z","z"]))
print(alienOrder(["z","z","x","z","z","z"]))
print(alienOrder(["z","z","x","z","z","z","z"]))
print(alienOrder(["z","z","x","z","z","z","z","z"]))
print(alienOrder(["z","z","x","z","z","z","z","z","z"]))
print(alienOrder(["z","z","x","z","z","z","z","z","z","z"]))
print(alienOrder(["z","z","x","z","z","z","z","z","z","z","z"]))