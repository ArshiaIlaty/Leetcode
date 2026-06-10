'''
Given a string s containing only lowercase English letters and the '?' character, convert all the '?' characters into lowercase letters such that the final string does not contain any consecutive repeating characters. You cannot modify the non '?' characters.

It is guaranteed that there are no consecutive repeating characters in the given string except for '?'.

Return the final string after all the conversions (possibly zero) have been made. If there is more than one solution, return any of them. It can be shown that an answer is always possible with the given constraints.
'''

def modifyString(s: str) -> str:
    if "?" in s:
        ind = s.find("?")
        print(ind)
        if ind == 0: pre = "a" 
        else: pre = s[ind-1]
        if ind == len(s) - 1: nex = "z" 
        else: nex = s[ind+1]
        print(pre, nex)
        rep = abs(ord(pre) - ord(nex))
        print(rep)
        print(chr(rep + 97))
        s = s.replace("?", chr(rep + 97))
        print(s)
    return s


def modify(s: str) -> str:
    for i in range(len(s)-1):
        if s[i] == "?":
            pre = s[i-1]
            nex = s[i+1]
            rep = abs(ord(pre) - ord(nex))
            s[i] = chr(rep + 97)
    return s

s = "?zs"
t = "j?qg??b"
modifyString(s)
modifyString(t) 
