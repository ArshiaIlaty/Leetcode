def minimumCost(cost: list[int]) -> int:
        cost.sort(reverse = True)
        print(cost)
        pay = 0
        i = 0
        while i < len(cost):
            pay += sum(cost[i : i + 2])
            i += 3
        print(pay)

        # for i in range(len(cost)):
        #     if i%3 != len(cost) % 3:
        #         pay += cost[i]
        #     i +=1
        # print(pay)
            # i += 2
            # for j in range(i+2, len(cost)):
            #     if cost[j]< min(cost[i] + cost[i+1]):
            #         cost.pop(j)
            #     elif len(cost) < 2:
            #         pay += sum(cost)
            #     else:
            #         j +=1

minimumCost(cost = [9,9,9,9])
minimumCost(cost = [6,5,7,9,2,2])
        