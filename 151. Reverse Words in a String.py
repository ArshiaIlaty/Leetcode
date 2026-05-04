def reverseWords(s: str) -> str:
    ss = s.split(" ")
    print(ss)
    ss.reverse()
    # ss = list(filter(None, ss))
    while("" in ss):
        ss.remove("")
    a = " ".join(ss)
    print(a)
    
reverseWords("the sky is blue")
