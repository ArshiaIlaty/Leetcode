def addBinary(self, a: str, b: str) -> str:
    for i in range(len(b)-1, -1,-1):
        str[i] = a[i] + b[i]
        if str[i]==2:
            a[i-1]+=1
            str[i]==0
    print str
            