def indexError(nums:list[int], target:int) -> int:
    l, r = 0, len(nums)-1
    while l <= r:
        mid = (l + r) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target and nums[mid+1] < target:
            l = mid + 1
    return -1

print(indexError([4, 5, 6, 7, 0, 1, 2], 0))

print(indexError([1,2,3,4,5], 3))
print(indexError([1,2,3,4,5], 6))
print(indexError([1,2,3,4,5], 0))
print(indexError([1,2,3,4,5], 7))
print(indexError([1,2,3,4,5], 8))
print(indexError([1,2,3,4,5], 9))
print(indexError([1,2,3,4,5], 10))