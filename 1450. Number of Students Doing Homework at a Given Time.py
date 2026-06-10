
def busyStudent( startTime: list[int], endTime: list[int], queryTime: int) -> int:
    counter = 0
    for (val1, val2) in zip(startTime, endTime):
        if (val1 <= queryTime <= val2):
            counter += 1
    print (counter)

    #or
    return sum([queryTime>=i and queryTime<=j for i, j in zip(startTime, endTime)])
busyStudent(startTime = [17], endTime = [86], queryTime = 39)