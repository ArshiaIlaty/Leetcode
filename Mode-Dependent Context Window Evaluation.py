def prepare_eval_input(tokens: list, mode: str, reserved_output: int) -> list:
    """
    Truncate a token list to fit the context window of the given reasoning mode.
    """
    # if mode == "non-think"
    # if mode == "high"
    # if mode == "max"
    context = {"non-think": 8192, "high": 131072, "max": 393216}
    if mode not in context:
        raise ValueError("Invalid mode")
    C = context[mode]
    L = C - reserved_output
    print(L)
    print(len(tokens))
    if L <= 0:
        return []
    elif len(tokens) > L:
        return tokens[::-L]
    elif len(tokens) <= L:
        return tokens
    
print(prepare_eval_input([1,2,3,4,5,6,7,8,9,10], "non-think", 10))
print(prepare_eval_input(list(range(10000)), "non-think", 192)[:3] + prepare_eval_input(list(range(10000)), "non-think", 192)[-3:])
print(len(prepare_eval_input(list(range(200000)), "high", 1072)))
print(len(prepare_eval_input(list(range(500000)), "max", 3216)))