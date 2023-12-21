def count_replacements(s):
    # count = 0 
    # for i in range(len(s) - 2):
    #     if s[i] == s[i+1] == s[i+2]:
    #         count += 1
    #         i = i + 2
    # return count


    res = 0
    con = 0
    for i in range(len(s) - 1):
        if s[i] == s[i+1]:
            con += 1
        elif con > 2:
            res += con // 3
            con = 1
    return res


# Example usage:
test_string = "baaaaaaaab"
result = count_replacements(test_string)
print(f"Number of replacements needed: {result}")