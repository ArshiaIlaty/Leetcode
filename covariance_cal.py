import numpy as np
def calculate_covariance_matrix(vectors: list[list[float]]) -> list[list[float]]:
	arr = np.array(vectors)
	print(arr)
	print('--------------------------------')
	cov_matrix = np.cov(arr, rowvar=True)
	print(cov_matrix)
	print('--------------------------------')
	return cov_matrix.tolist()
	# mean = []
	# m = len(vectors) # of observation
	# res = []
	# for i in range(len(vectors)):
	# 	m = sum(vectors[i])/len(vectors)
	# 	mean.append(m)
	# 	s = 0
	# 	for j in range(len(vectors[0])):
	# 		s+=(vectors[i][j]-mean[i])**2
	# 	mini = []
	# 	for k in range(len(vectors)):
	# 		co = np.cov(vectors[i],vectors[k])
	# 		mini.append(co)
	# 	res.append(mini)
	# return res

print(calculate_covariance_matrix([[1,2,3],[2,3,4],[5,6,7]]))

print(calculate_covariance_matrix([[1, 2, 3], [4, 5, 6]]))