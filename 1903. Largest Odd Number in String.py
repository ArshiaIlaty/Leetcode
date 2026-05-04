def largestOddNumber(num: str) -> str:
    if int(num[-1])%2 != 0:
        return num
    else:
        l = 0
        r = l+1
        n = list(num[::-1])
        for i in range(1, len(n)):
            if int(n[i]) % 2 == 0:
                n[0], n[i] = n[i], n[0]  
                break
        return ''.join(n)
            
print(largestOddNumber(num = "2406"))    
print(largestOddNumber(num = "52"))