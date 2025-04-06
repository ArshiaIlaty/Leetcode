'''
You have a bomb to defuse, and your time is running out! Your informer will provide you with a circular array code of length of n and a key k.

To decrypt the code, you must replace every number. All the numbers are replaced simultaneously.

If k > 0, replace the ith number with the sum of the next k numbers.
If k < 0, replace the ith number with the sum of the previous k numbers.
If k == 0, replace the ith number with 0.
As code is circular, the next element of code[n-1] is code[0], and the previous element of code[0] is code[n-1].

Given the circular array code and an integer key k, return the decrypted code to defuse the bomb!
'''

def decrypt(code: list[int], k: int) -> list[int]:
    res = []
    if k > 0:
        for i in range(0, len(code), 1):
            print(code[i+1:i+1+k])
            l = code[i+1:i+1+k]
            s = sum(code[i+1:i+1+k]) 
            if len(code) - i - 1 < k:
                s = s + sum(code[l-i-1:i-1])
            res.append(s)

    elif k < 0:
        for i in range(0, len(code)-1, 1):
            s = sum(code[:i]) + sum(code[i+2:])
            res.append(s)
        res.append(sum(code[1:-1]))  # for the last element

    elif k == 0:
        return [0]*len(code)
    print(res)
    return res
one = decrypt(code = [5,7,1,4], k = 3)
sec = decrypt(code = [1,2,3,4], k = 0)
thi = decrypt(code = [5,2,2,3,1], k = 3)
forth = decrypt(code =[2,4,9,3], k = -2)
print(sec)
print(forth)
print(thi)

