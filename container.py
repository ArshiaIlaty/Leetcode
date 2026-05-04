'''
"Does the width of the line matter? Or is it purely the index distance (j - i)?" (Usually purely index).

'''
def contain(height:list[int]) -> int:
    l = 0
    r = len(height)-1
    max_area = 0
    while l<r:
        max_area = max(max_area, min(height[l], height[r])*(r-l))
        if height[l] < height[r]:
            l += 1
        else:
            r -= 1
    return max_area

print(contain([1,8,6,2,5,4,8,3,7]))
