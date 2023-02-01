def countGoodRectangles(rectangles: list[list[int]]) -> int:
    large = []
    t = 0
    for rec in rectangles:
        mi = min(rec[0], rec[1])
        large.append(mi)
        t = large.count(max(large))
    print(t)
   
    # res = []
    # for i in large:
    #     t = large.count(i)
    #     res.append(t)
    #     res.sort()
    # print(res[-1])


countGoodRectangles(rectangles = [[5,8],[3,9],[5,12],[16,5]])