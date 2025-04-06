'''
Given an array of integers, write a function min_distance to calculate the minimum absolute distance between two elements 
then return all pairs having that absolute difference.

Note: Make sure to return the pairs in ascending order.'''
# from typing import List
def min_distance(nums:list[int], min_distance:int)->list[list[int]]:
    pairs = []
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if abs(nums[i] - nums[j]) == min_distance:
                pairs.append([nums[i], nums[j]])
    print(pairs)
    return pairs

print(min_distance([1, 3, 5, 7, 9], 2))  # Expected output: [[1, 3], [3, 5], [5, 7], [7, 9]]