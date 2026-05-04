import heapq

def meetingrooms(rooms:list[list[int]]) -> int:
    # Sorting by start time
    rooms.sort(key=lambda x: x[0])
    print(rooms)
    end = [i[1] for i in rooms]
    # Heapify the end times to get the minimum end time
    heapq.heapify(end)
    print(end)
    for room in rooms:
        # If the start time of the current room is greater than or equal to the minimum end time,
        # then we can use the same room and pop the minimum end time
        if room[0] >= end[0]:
            heapq.heappop(end)
            print(end)
        # If the start time of the current room is less than the minimum end time,
        # then we need to push the end time of the current room to the heap
        heapq.heappush(end, room[1])
        print(end)
    # The number of rooms needed is the length of the heap minus the length of the rooms
    return len(end)-len(rooms)

print(meetingrooms([[0, 30], [10, 20], [20, 30], [5, 10], [15, 20]]))

