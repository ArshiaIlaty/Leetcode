def mapWordWeights(words: list[str], weights: list[int]) -> str:
# a = 97
    s = ''
    for word in words:
        w = 0
        for ch in word:
            w += weights[abs(97 - ord(ch))]
            print(ch)
            print(w)
        s += chr(122 - w % 26)
        print(s)
    return s

mapWordWeights(["abcd","def","xyz"], [5,3,12,14,1,2,3,2,10,6,6,9,7,8,7,10,8,9,6,9,9,8,3,7,7,2])
mapWordWeights(["a","b","c"],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1])
mapWordWeights(["abcd"],[7,5,3,4,3,5,4,9,4,2,2,7,10,2,5,10,6,1,2,2,4,1,3,4,4,5])