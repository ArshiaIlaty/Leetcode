from collections import defaultdict

def groupAnagrams(strs: list[str]) -> list[list[str]]:
    # map: Key is Tuple(counts), Value is List of strings
    # anagram_map = defaultdict(list)
    anagram_map = {}
    
    for s in strs:
        # 1. Create the "Signature" (Count array)
        count = [0] * 26 
        
        for char in s:
            # Map 'a'->0, 'b'->1, etc.
            # ord('a') gives the ASCII value of 'a'
            count[ord(char) - ord('a')] += 1
            print(count)
            
        # 2. Convert list to Tuple to use as Key (Immutable)
        key = tuple(count)
        print(key)
        
        # 3. Group it
        anagram_map[key].append(s)
        print(anagram_map)
    # 4. Return just the groups (the values)
    print(list(anagram_map.values()))
    return list(anagram_map.values())

print(groupAnagrams(["eat","tea","tan","ate","nat","bat","ac","ca","abc","cba","bac","bca","cab","abc"]))

