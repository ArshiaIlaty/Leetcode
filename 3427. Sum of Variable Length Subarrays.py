def subarraySum(nums: list[int]) -> int:
    s = 0
    for i in range(len(nums)):
        s += sum(nums[max(0, i - nums[i]):i+1])
        print(s)
        print('--------------------------------')
    return s

print(subarraySum([2,3,1]))
print(subarraySum([3,1,1,2]))
print(subarraySum([1,2,3]))