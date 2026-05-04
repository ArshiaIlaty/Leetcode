import heapq

def findKthLargest(nums: list[int], k: int) -> int:
    # initiate the heap with the first k elements
    heap = nums[:k]
    heapq.heapify(heap) 
    # building the heap takes O(k) time
    # push the rest of the elements into the heap
    # if the element is greater than the root, replace the root with the element
    # and heapify the heap
    # this takes O((n-k)log(k)) time
    print(heap)
    for num in nums[k:]:
        if num > heap[0]:
            heapq.heappop(heap)
            heapq.heappush(heap, num)
            print(heap)
    # return the root of the heap
    return heap[0]

print(findKthLargest([3,2,1,5,6,4], 2))
print(findKthLargest([3,2,3,1,2,4,5,5,6], 4))

# max heap
# import heapq

def find_kth_smallest(arr, k):
    # Python's heapq is a min-heap. We can simulate a max-heap
    # by storing negative values of the elements.
    max_heap = []
    
    # 1. Insert initial k elements (as negative)
    for i in range(k):
        heapq.heappush(max_heap, -arr[i])
        # or before for loop, heap = arr[:k] and heapq.heapify(heap)
        print(max_heap)
    print('--------------------------------')
    # 2. Process remaining elements
    for i in range(k, len(arr)):
        if -arr[i] > max_heap[0]: # Compare current element with heap root
            heapq.heappop(max_heap)
            heapq.heappush(max_heap, -arr[i])
            print(max_heap)
    # 3. The root of the max heap (after negating back) is the k-th smallest element
    return -max_heap[0]

print(find_kth_smallest([3,2,1,5,6,4], 2))
print(find_kth_smallest([3,2,3,1,2,4,5,5,6], 4))