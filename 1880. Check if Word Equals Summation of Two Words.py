class Solution:
    def isSumEqual(firstWord: str, secondWord: str, targetWord: str) -> bool:
        w1 = ""
        w2 = ''
        t = ''
        for char in firstWord.lower():
            s = ord(char) - 97
            w1 += str(s)
            print(w1)
        for char in secondWord.lower():
            s = ord(char) - 97
            w2 += str(s)
            print(w2)
        for char in targetWord.lower():
            s = ord(char) - 97
            t += str(s)
            print(t)
        return int(w1) + int(w2) == int(t)
        # if int(w1) + int(w2) == int(t):
        #     return True
        # return False
            
    isSumEqual(firstWord ="acb", secondWord ="cba", targetWord ="cdb")