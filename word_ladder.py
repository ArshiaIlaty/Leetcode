'''
The "Google" Optimization: Instead of checking every single word in the dictionary to find neighbors (which is O(N * L)), use a Wildcard Map.
Wildcard Map: A map of words with wildcard characters replaced by all possible characters.
For example, "d_g" -> ["dog", "dig", "dag", "dpg", "etc."].
This reduces the search space from O(N * L) to O(M * L), where M is the number of words in the Wildcard Map.
The Wildcard Map is built once, and then used for each word in the dictionary to find neighbors.
The Wildcard Map is built using a trie data structure.
'''
def 