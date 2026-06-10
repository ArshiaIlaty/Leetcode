def processQueries(queries: list[int], m: int) -> list[int]:
    per = [i for i in range(1, m +1)]
    res = []
    for i in range(len(queries)):
        num = queries[i]
        pos = per.index(num)
        res.append(pos)
        per.remove(num)
        per.insert(0, num)
    print(res)





processQueries(queries = [3,1,2,1], m = 5)