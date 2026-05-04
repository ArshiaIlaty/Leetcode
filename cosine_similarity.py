import numpy as np

def cosine_similarity(vec1, vec2):
	"""
	Calculate the cosine_similarity of two vectors.
	Args:
		vec1 (numpy.ndarray): 1D array representing the first vector.
		vec2 (numpy.ndarray): 1D array representing the second vector.
	Returns:
		The cosine_similarity of the two vectors.
	"""
	# Implement your code here
	s = 0
	one_l = 0
	two_l = 0
	for i in range(len(vec1)):
		s += vec1[i]*vec2[i]
		one_l += vec1[i]**2
		two_l += vec2[i]**2
	return s/(np.sqrt(one_l)*np.sqrt(two_l))


v1 = np.array([1, 2, 3])
v2 = np.array([2, 4, 6])
print(round(cosine_similarity(v1, v2), 3))