
x = pow(317, 47) % 467
y = (13//14) % 11
print(x)
print(y)

for i in range(50):
    if (*i) % 11 == 3:
        print(i)

# def computeGCD(x, y):
 
#     while(y):
#        x, x = y, x % y
#     return abs(x)
 
# a = 791291
# b = 402
 
# print (computeGCD(791291, 402))

new = [0]*10
print(new)
for i in range(1, 10):
    new.append(i)
print(new)
#you can not pop elements from the specific index to another index
# new.pop(0:10)
del new[0:10]
print(new)