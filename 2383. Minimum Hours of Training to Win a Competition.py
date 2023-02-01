def minNumberOfHours(initialEnergy: int, initialExperience: int, energy: list[int], experience: list[int]) -> int:
    # leng, opponent = len(energy)
    totene = sum(energy)
    totexp = 0
    neededenergy = 0
    if totene >= initialEnergy:
        neededenergy = (totene - initialEnergy) + 1
    else:
        neededenergy = 0
    for i in range(len(experience)):
        if initialExperience <= experience[i]:
            totexp += (experience[i] - initialExperience) + 1
            initialExperience = experience[i] + 1
        initialExperience += experience[i]
    print (neededenergy + totexp)


minNumberOfHours(initialEnergy = 1, initialExperience = 1, energy = [1,1,1,1], experience = [1,1,1,50])