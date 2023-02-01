def numberOfBeams(bank: list[str]) -> int:
    print('0'*len(bank[0]))
    x = str('0'*len(bank[0]))
    if x in bank: bank.remove(x)
    print(bank)
    for row in range(len(bank)):
        for col in range(len(bank[0])):
            # if bank[cal][row] == '1':

                print(bank[row][col])


    for row in bank:
        for cal in row:
            # if bank[cal][row] == '1':

            print(cal)

    # new = []
    # res = 0
    # for i in bank:
    #     t = i.count('1')
    #     if t != 0:
    #         new.append(t)
    # for j in range(len(new)-1):
    #     res += new[j]*new[j+1]
    # print(res)
    # return res



numberOfBeams(bank = ["011001","000000","010100","001000"])