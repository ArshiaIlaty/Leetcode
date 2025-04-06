def merge(intervals: list[list[int]]) -> list[list[int]]:
    res = []
    inde = []
    intervals.sort()
    for i in range(len(intervals)-1):
        if intervals[i][1] >= intervals[i+1][0]:
            intervals[i+1] = [min(intervals[i][0], intervals[i+1][0]), max(intervals[i][1], intervals[i+1][1])]
            print("min", min(intervals[i][0], intervals[i+1][0]))
            print("max", max(intervals[i][1], intervals[i+1][1]))
            print(intervals)
            inde.append(i)
            res.append([min(intervals[i][0], intervals[i+1][0]), max(intervals[i][1], intervals[i+1][1])])
            print(inde)
            print(intervals)
            print(res)
    for i in reversed(inde):
        del res[i]
        print(res)
    for i in reversed(inde):
        intervals.pop(i)
    print(intervals)
    print(res)
    return intervals

# first = merge(intervals= [[1,3],[2,6],[8,10],[15,18]])
# second = merge(intervals= [[1,4],[4,5]])
third = merge(intervals =[[1,4],[0,2],[3,5]])