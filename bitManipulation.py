def bit(nums:list[int]) -> int:
    res = 0
    for num in nums:
        res = res ^ num
        print(res)
    return res

print(bit([1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,15,15]))

