def compress(chars: list[str]) -> int:
    # s = " "
    # l = 0
    # for i in range(len(chars)-1):
    #     if chars[i] != chars[i+1]:
    #         s += chars[i]
    #         print(s)
    #     if chars[i] == chars[i+1]:
    #         l += 1
    # s += str(l)
    # s += chars[i]
    # print(s)
    # return len(s)
    insert = 0
    i = 0
    while i < len(chars):
        l = 1
        while chars[i] == chars[i+l] and i+l < len(chars):
            l += 1
        chars[insert] = chars[i]
        insert += 1
        if l > 1:
            chars[insert:insert+len(str(l))] = str(l)
            insert += len(str(l))
        i += l
    return insert
#         i
#         ins
# ["a","a","b","b","c","c","c"]
#   0    1   2   3   4   5   6 

comp = compress(chars = ["a","a","b","b","c","c","c"])
comp1 = compress(chars = ["a","b","b","b","b","b","b","b","b","b","b","b","b"])