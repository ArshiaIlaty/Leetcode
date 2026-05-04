def calculate_matrix_mean(matrix: list[list[float]], mode: str) -> list[float]:

	res = []
	if mode == 'row':
		for i in range(len(matrix)):
      	    s = 0
		    s += sum(matrix[i])/len(matrix)
			print(s)
		res.append(s)
		print(res)
		print('--------------------------------')
	else:
		for i in range(len(matrix)):
			for j in range(len(matrix[0])):
                s = 0
				s += matrix[j][i]
				print(s)
			res.append(s/len(matrix[0]))
			print(res)
			print('--------------------------------')
	return res


print(calculate_matrix_mean([[1, 2, 3], [4, 5, 6], [7, 8, 9]], 'column'))