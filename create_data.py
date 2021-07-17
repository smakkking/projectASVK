import json
import random

M = 16 # число процессоров
N = M * 8 # число программ

PROG_CHANCE = {
    5: 65,
    10: 20,
    15: 10,
    20: 5,
} # распределение вероятностей для нагрузок программ
PROC_CHANCE = {
    50: 5,
    70: 15,
    90: 40,
    100: 30
} # распределение вероятностей для максимальной нагрузки процессоров

PROC_CHOICE = []
for x, y in PROC_CHANCE.items():
    PROC_CHOICE.extend([x] * y)

PROG_CHOICE = []
for x, y in PROG_CHANCE.items():
    PROG_CHOICE.extend([x] * y)

INTENSE_CHOICE = [0, 10, 50, 70, 100]

d_ex = {}

MIN_CONNECT = 2 # минимальная степень вершины в графе связей программ через сеть
for i in range(N):
    for _ in range(MIN_CONNECT):
        t1 = i + 1
        t2 = random.randint(1, N)
        if (t1, t2) in d_ex.keys() or (t2, t1) in d_ex.keys() or t1 == t2:
            continue
        d_ex[
            (t1, t2)
        ] = random.choice(INTENSE_CHOICE)

X = [0]
Y = [1]
while sum(X) < sum(Y):
    X = [random.choice(PROC_CHOICE) for _ in range(M)]
    Y = [random.choice(PROG_CHOICE) for _ in range(N)]

data = {
    'proc': {
        'len': M,
        'max_load': X
    },
    'programs': {
        'len': N,
        'load': Y
    },
    'data_exchange': [
        {
            'pr1': x,
            'pr2': y,
            'intensity': value
        } for ((x, y), value) in d_ex.items()
    ]
}

with open('input.json', 'w') as f:
    json.dump(data, f, indent=4)

print(
    'STATS',
    f'proc_len= {M}',
    f'prog_len= {N}',
    f'connections= {len(d_ex)}',
    sep='\n'
)