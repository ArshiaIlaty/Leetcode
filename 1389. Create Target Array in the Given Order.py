def createTargetArray(nums: list[int], index: list[int]) -> list[int]:
    
    List = []
    min = min(len(index), len(nums))
    for i in range(min):
        List.insert(index[i], nums[i])
    print(List)

createTargetArray(nums = [1,2,3,4,0], index = [0,1,2,3,0])    
    