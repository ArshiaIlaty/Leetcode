def sortSentence(s: str) -> str:
    new = s.split(' ')
    print(new)
    result = sorted(new, key=lambda x: x[-1])
    for i in range(0, len(new) - 1):
        result = result[i].delete(-1)
    print (result)
    a = ' '.join(result)
    print(a)
    
            
sortSentence(s = "is2 sentence4 This1 a3")