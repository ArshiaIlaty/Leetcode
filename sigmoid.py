import math

def sigmoid(z: float) -> float:
	return 1/(1+math.exp(-z))

print(sigmoid(0))
print('--------------------------------')
print(sigmoid(1))
print('--------------------------------')
print(sigmoid(2))
print('--------------------------------')
print(sigmoid(3))
print('--------------------------------')
print(sigmoid(4))
print('--------------------------------')
print(sigmoid(5))
print('--------------------------------')