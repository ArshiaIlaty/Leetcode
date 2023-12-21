def minCost(colors: str, neededTime: list[int]) -> int:
    res = 0
    i = 0
    for i in range(len(colors) - 1):
        if colors[i] == colors[i+1] and i < len(neededTime) - 1:
            if neededTime[i] >= neededTime[i+1]:
                res += neededTime[i+1]
                #colors = colors[:i+1] + colors[i+2:]
                print(colors)
            else:
                res += neededTime[i]
                #colors = colors[:i] + colors[i+1:]
                print(colors)
    print(res)
    return res

minCost(colors = "abaac", neededTime = [1,2,3,4,5])
minCost(colors = "aabaa", neededTime = [1,2,3,4,1])
minCost(colors = "aaabbbabbbb", neededTime = [3,5,10,7,5,3,5,5,4,8,1])


'''
class Solution:
    def minCost(self, colors: str, neededTime: List[int]) -> int:
        res = 0
        i = 0
        for i in range(len(colors) - 1):
            if colors[i] == colors[i+1] and i < len(neededTime) - 1:
                res += min(neededTime[i], neededTime[i+1])
                neededTime[i+1] = max(neededTime[i], neededTime[i+1])
        return res
'''