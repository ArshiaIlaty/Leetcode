def longest_substring(s:str, k:int) -> int:
    l = 0
    r = l+1
    res = []
    while l<r<len(s)+1:
        s = s[l:r]
        if len(set(s)) <= k:
            res.append(s)
            r += 1
        else:
            l += 1
    return max(len(sub_string) for sub_string in res)

print(longest_substring("eceba", 2))