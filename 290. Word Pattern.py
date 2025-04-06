def wordPattern(pattern: str, s: str) -> bool:
    ss = s.split(' ')
    if len(ss)!=len(pattern):
        return False
    dict = {}
    for i in range(len(ss)):
        print(ss)
        print(dict)
        if ss[i] not in dict:
            dict[ss[i]] = pattern[i]
        elif dict[ss[i]]!= pattern[i]:
            return False
    if len(set(dict.values())) != len(dict.values()):
            return False
    return True
print(wordPattern("abba", "dog dog dog dog"))
print(wordPattern("abba", "dog cat cat dog"))
print(wordPattern("aaaa", "dog cat cat dog"))
print(wordPattern("abba", "dog cat cat fish"))