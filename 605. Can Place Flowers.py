'''
You have a long flowerbed in which some of the plots are planted, and some are not. However, flowers cannot be planted in adjacent plots.

Given an integer array flowerbed containing 0's and 1's, where 0 means empty and 1 means not empty, and an integer n, return true if n new flowers can be planted in the flowerbed without violating the no-adjacent-flowers rule and false otherwise.
'''

def canPlaceFlowers(flowerbed: list[int], n: int) -> bool:
    # for i in range(len(flowerbed)-1):
    #     if flowerbed[i] == 0 and flowerbed[i+1] == 0 and flowerbed[i-1] == 0:
    #         n -= 1
    #         flowerbed[i] = 1
    #         print(flowerbed)
    #         print(n)
    # return n == 0

# (Handle Edges Properly)
    length = len(flowerbed)

    for i in range(length):
        if flowerbed[i] == 0:
            left = (i == 0) or (flowerbed[i-1] == 0)
            right = (i == length-1) or (flowerbed[i+1] == 0)
            print(left, right)

            if left and right:
                flowerbed[i] = 1
                n -= 1
                print(flowerbed)
                print(n)
                if n <= 0:
                    return True

    return n <= 0

print(canPlaceFlowers([0,0,1,0,1], 1))
print(canPlaceFlowers([1,0,0,0,1], 1))
print(canPlaceFlowers([1,0,0,0,1], 2))
print(canPlaceFlowers([1,0,0,0,1], 3))
print(canPlaceFlowers([1,0,0,0,1], 4))
print(canPlaceFlowers([1,0,0,0,1], 5))
print(canPlaceFlowers([1,0,0,0,1], 6))
print(canPlaceFlowers([1,0,0,0,1], 7))