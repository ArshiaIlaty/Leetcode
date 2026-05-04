def maxOperations(nums: list[int], k: int) -> int:
    nums.sort()
    l = 0
    r = len(nums)-1
    res = 0
    while l<r:
        if nums[l] + nums[r] == k:
            res += 1
            l += 1
            r -= 1
        elif nums[l] + nums[r] < k:
            l += 1
        else:
            r -= 1