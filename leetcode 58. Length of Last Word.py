# def lengthOfLastWord(s: str) -> int:
#     print(len(s.split()[-1]))

# lengthOfLastWord('hello my man')    

def lengthOfLastWord( s: str) -> int:
    
    counter = 0

#this is help you to comeback from the end of the string
    for i in range(len(s)-1, -1, -1):
        if s[i]!= ' ':
            counter +=1  
        elif counter > 0: 
            break
    print (counter)

lengthOfLastWord('hello my man')
    