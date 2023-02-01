from numpy import insert


def addBinary( a: str, b: str) -> str:
    op = ''
    c = 0
    # for i in range(len(b)-1, -1,-1):
    #     c = a[i] + b[i]
    #     c.str()
    #     insert.str(c)
    #     if str[i]==2:
    #         a[i-1]+=1
    #         str[i]==0
    # print (str)

    for i in range(len(b)-1, -1,-1):
        c = int(a[i]) + int(b[i])
        if c==2:
            a[i-1] = str((int(a[i-1])+1)%2)
            op[i] == '0'
        else:
            op.insert(str(c))
    print (op)
        

addBinary(a='11', b='1')            