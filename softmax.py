import numpy as np

def softmax(scores: list[float]) -> list[float]:
    scores = np.array(scores)
    print(scores)
    print('--------------------------------')
    # Numerical stability
    scores = scores - np.max(scores)
    print(scores)
    print('--------------------------------')
    exp_scores = np.exp(scores)
    print(exp_scores)
    print('--------------------------------')
    probabilities = exp_scores / np.sum(exp_scores)
    print(probabilities)
    print('the final result--------------------------------')
    return probabilities.tolist()


print([round(x, 4) for x in softmax([1, 2, 3])])