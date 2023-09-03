from random import randint

a = [1, 2, 3, 4]

i = randint(0, len(a) - 1)
t = a.pop(randint(0, len(a)))
j = a.pop(randint(0, len(a)))


print(t, j)