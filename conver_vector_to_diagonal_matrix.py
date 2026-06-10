import numpy as np

def make_diagonal(x):
	m = len(x)
	# res = [[0 for _ in range(m)] for _ in range(m)]
	res = [[0] * m for _ in range(m)]
	print(res)
	print('--------------------------------')
	for i in range(m):
		res[i][i] = x[i]
		print(res)
		print('--------------------------------')
	return res

print(make_diagonal(np.array([1, 2, 3])))