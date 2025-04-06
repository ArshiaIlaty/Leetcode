def lengthOfLongestSubstring(s: str) -> int:
    res = set()
    l = 0
    m = 0
    for r in range(len(s)):
        while s[r] in res:
            res.remove(s[l])
            l += 1
        res.add(s[r])
        m = max(r - l + 1, m)
    print(m)
    print('----------------------------------------------------------------')
    return m

A = lengthOfLongestSubstring(s = "pwwkew")
B = lengthOfLongestSubstring(s = "abcabcbb")
C = lengthOfLongestSubstring(s = "bbbbb")
D = lengthOfLongestSubstring(s = "aab")
E = lengthOfLongestSubstring(s = "dvdf")
F = lengthOfLongestSubstring(s = "abad")