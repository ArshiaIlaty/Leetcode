'''
Notes: # For alphabet
>>> 'A'.isdigit()
False
>>> 'A'.isalpha()
True

# Removing spaces
value = int(" 42 ".strip())
print(value)

If you want to remove leading and ending whitespace, use str.strip()

return statement1 if expression1 else (statement2 if expression2 else statement3)

ValueError: invalid literal for int() with base 10: ''
How to fix it?
int(float('55063.000000'))
'''

def myAtoi(s: str) -> int:
    s.strip()
    s.lstrip('0')
    sign = ''
    if s[0] == '-' or s[0] == '+':
        sign = s[0]
        s = s[1:]
        print(sign)
    for i in range(len(s)):
        if s[i].isdigit() == False:
            num = int(s[0:i])
            print(num)
            if sign == '-':
                return -num
    num = int(s)
    print(num)
    return -num if sign == '-' else num


A = myAtoi(s = "1337c0d3")