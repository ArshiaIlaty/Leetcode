from collections import Counter, defaultdict
import heapq
def top(nums:list[int], k:int ) ->list[int]:
    d = defaultdict(int)
    for num in nums:
        d[num] += 1
    print(d)
    heap = []
    #  Time complexity: nlog(k) same as a binary search or binary insert
    for key, val in d.items():
        if len(heap) < k or val > heap[0][0]:
            heapq.heappush(heap, [val, key])
            print(heap)
        if len(heap) > k:
            heapq.heappop(heap)
    print([x[1] for x in heap] )
    return [x[1] for x in heap]        
    #     heapq.heappush(heap, (-val, key))
    #     if len(heap) > k:
    #         heapq.heappop(heap)
    # return [-x[1] for x in heap]
    # c = Counter(nums)
    # print(c)
    # print(sorted(c.values(), reverse=True))
    # print(c[k])
    
first = top(nums=[11,1,1,2,2,2,3,3,3,3,3,4], k = 3)