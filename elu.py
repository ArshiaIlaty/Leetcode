import math

# alpha is a hyperparameter that controls the slope of the negative part of the function, typically set to 1.0

def elu(z: float, alpha: float) -> float:
	return z if z > 0 else alpha*(math.exp(z)-1)

print(elu(0, 1))
print('--------------------------------')
print(elu(1, 1))
print('--------------------------------')
print(elu(2, 1))
print('--------------------------------')
print(elu(3, 1))
print('--------------------------------')
print(elu(4, 1))
print('--------------------------------')
print(elu(5, 1))

'''
Notes:
- ELU is a smooth activation function that is similar to ReLU, but has a slope for negative values.
- ELU is more robust to noise than ReLU.
- ELU is more computationally expensive than ReLU.
- ELU is more sensitive to the value of alpha.
vs. ReLU: ELU avoids the "dying ReLU" problem and provides higher accuracy in deep networks by capturing negative information. However, ELU is computationally more expensive due to the exponential operation.
vs. Leaky ReLU: While both prevent dying neurons, ELU has a smoother curve, allowing for better noise-robust deactivation.
'''