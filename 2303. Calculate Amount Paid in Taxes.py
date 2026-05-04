def calculateTax(brackets: list[list[int]], income: int) -> float:
    tax = 0
    if income >=  brackets[0][0]:
        tax += brackets[0][0]*(brackets[0][1]/100)
        print(tax)
        income -= brackets[0][0]
        print(income)
    else:
        tax += income*(brackets[0][1]/100)
        print(tax)
    for i in range(1, len(brackets)):
        if income - (brackets[i][0] - brackets[i-1][0]) >= 0:
            tax += (brackets[i][0] - brackets[i-1][0])*(brackets[i][0]/100)
            income -= brackets[i][0] - brackets[i-1][0]
            print(tax)
            print(income)
        else:
            tax += income*(brackets[i][0]/100)
            print(tax)
            print(income)
    return tax




# two pointer approach
def calculateTax(brackets: list[list[int]], income: int) -> float:
    tax = 0
    l = 0
    r = 1
    while l < len(brackets):
        if income - (brackets[r][0] - brackets[l][0]) >= 0:
            tax += (brackets[r][0] - brackets[l][0])*(brackets[r][0]/100)
            income -= brackets[r][0] - brackets[l][0]
            
            
print(calculateTax([[3,50],[7,10],[12,25]], 10))
print(calculateTax([[1,0],[4,25],[5,50]], 2))
print(calculateTax([[2,50]], 0))