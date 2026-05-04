def minSubArrayLen(target: int, nums: list[int]) -> int:
    l = 0
    r = l+1
    res = []
    while l<r<len(nums)+1:
        s = sum(nums[l:r])
        if s < target:
            r += 1
        elif s >= target:
            res.append(nums[l:r])
            l+=1
            r = l+1
    print(res)
    if len(res) > 0 :
        m = min(len(sub_array) for sub_array in res)
    else: m = 0
    return m

# print(minSubArrayLen(7, [2,3,1,2,4,3]))
# print(minSubArrayLen(4, [1,4,4]))
# print(minSubArrayLen(11, [1,1,1,1,1,1,1,1]))
print(minSubArrayLen(6,[10,2,3]))
print(minSubArrayLen(15,[5,1,3,5,10,7,4,9,2,8]))
