# We can do the whole thing manually (without split()).
# Idea:
# initilialize two pointers, l and r.
# Move the right pointer as long as it's not pointing to the whitespace.
# If it finally points to the whitespace, we have a word. Take this word by using slicing, reverse it, and add to res.
# Move r and l. Now they point to the character after the whitespace (essentially, it's where the next word starts).

# Once the loop ends, we have the last word unproccessed.
# Need to add it manually.
# Add an extra space to res (because l always points to the first character of a word).
# Add the reversed word to res.
# Finally, res has one extra whitespace in the beginning. It appeared when we were appending the first word. But you can account for this in your return statement.

def reverseWords_manual(s):  # O(n) both
    res = ''
    l, r = 0, 0
    while r < len(s):
        if s[r] != ' ':
            r += 1
        elif s[r] == ' ':
            res += s[l:r + 1][::-1]
            r += 1
            l = r
    res += ' '
    res += s[l:r + 2][::-1]
    print(res[1:])


reverseWords_manual('Arshia Ilaty')