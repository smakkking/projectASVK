import random
import json
import copy
from multiprocessing import Process, Value, Array, Queue
import time
import sys

MAX_IT = 1000

class SolveX:
    def __init__(self):
        try:
            with open(sys.argv[1], 'r') as f:
                data = json.load(f)
        except:
            raise InputError

        self.N = data['programs']['len']
        if not (type(self.N) == int and self.N >= 1):
            raise InputError

        self.M = data['proc']['len']
        if not (type(self.M) == int and self.M >= 1):
            raise InputError

        self.N_load = data['programs']['load']
        if not (type(self.N_load) == list and len(self.N_load) == self.N):
            raise InputError
        for x in self.N_load:
            if not (type(x) == int and x > 0):
                raise InputError

        self.M_max_load = data['proc']['max_load']
        if not (type(self.M_max_load) == list and len(self.M_max_load) == self.M):
            raise InputError
        for x in self.M_max_load:
            if not (type(x) == int and x > 0):
                raise InputError

        self.data_exchange = {}
        try:
            for x in data['data_exchange']:

                if not (type(x['intensity']) == int and x['intensity'] >= 0) or \
                        not (type(x['pr1']) == int and 0 <= x['pr1'] <= self.N) or \
                        not (type(x['pr2']) == int and 0 <= x['pr2'] <= self.N):
                    raise InputError
                self.data_exchange[
                    (x['pr1'], x['pr2'])
                ] = x['intensity']
                self.data_exchange[
                    (x['pr2'], x['pr1'])
                ] = x['intensity']
        except:
            raise InputError

        self.solve = []
        self.true_solve = []

    def generate_solve(self):
        """получает случайное решение"""
        self.solve = [random.randint(1, self.M) for _ in range(self.N)]

    def check_solve(self):
        """проверка условий коррекности решения(ограничения по нагрузке на процессоры)"""
        t = copy.deepcopy(self.M_max_load)
        for (i, x) in enumerate(self.solve):
            t[x - 1] -= self.N_load[i]

        flag = True
        for x in t:
            flag &= x >= 0
        return flag

    def calc_intensity(self):
        """общая нагрузка на сеть для данного размещения программ по процессорам"""
        result = 0
        for ((x1, y1), value) in self.data_exchange.items():
            if self.solve[x1 - 1] != self.solve[y1 - 1]:
                result += value
        return result / 2

    def iterate_seq(self):
        """базовый алгоритм"""
        self.F_min = sum(self.data_exchange.values()) / 2

        end_it = 0
        self.all_it = 0

        while (end_it != MAX_IT and self.F_min != 0):
            try:
                end_it += 1
                self.generate_solve()
                F = self.calc_intensity()
                if F < self.F_min:
                    if self.check_solve():
                        self.all_it += end_it
                        end_it = 0
                        self.F_min = F
                        self.true_solve = self.solve
            except KeyboardInterrupt:
                break
        self.all_it += end_it

    def formated_solve(self):
        s = ''
        for x in self.true_solve:
            s += str(x) + ' '
        return s

    def show_info(self):
        """выводит всю информацию, полученную после работы базового алгоритма"""
        if self.F_min == sum(self.data_exchange.values()) / 2:
            self.true_solve = [-1 for _ in range(self.N)]
            print('failure',
                  self.all_it,
                  sep='\n'
                  )
        else:
            print('success',
                  self.all_it,
                  self.formated_solve(),
                  self.F_min,
                  sep='\n'
                  )
            if 'proc_load' in sys.argv:
                t = [0 for _ in range(self.M)]
                for i, x in enumerate(self.true_solve):
                    t[x - 1] += self.N_load[i]
                t = [t[i] / self.M_max_load[i] * 100 for i in range(self.M)]
                print(f'percent of load proc= {t}')

    def iterate_parall(self, true_solve, F_min, QUEUE):
        """многопоточный алгоритм"""
        end_it = 0
        all_it = 0

        while (end_it != MAX_IT and F_min != 0):
            try:
                end_it += 1
                self.generate_solve()
                F = self.calc_intensity()
                if F < F_min.value:
                    if self.check_solve():
                        all_it += end_it
                        end_it = 0

                        F_min.value = F

                        QUEUE.put(1, block=True)
                        for i in range(self.N):
                            true_solve[i] = self.solve[i]
                        QUEUE.get()
            except KeyboardInterrupt:
                if QUEUE.full():
                    QUEUE.get()
                break
        all_it += end_it


def get_best(true_solve, F_min, QUEUE):
    X = SolveX()
    X.iterate_parall(true_solve, F_min, QUEUE)


def seq_mode(mn=1):
    if mn != 1:
        random.seed(mn)
    else:
        random.seed()
    duration = time.time()
    X = SolveX()

    # если базовый алгоритм нужно запустить несколько раз подряд( и взять лучшее решение)
    if mn != 1:
        F_min = sum(X.data_exchange.values()) / 2
        true_solve = []
        all_it = 0
        for _ in range(mn):
            X.iterate_seq()
            if X.F_min < F_min:
                F_min = X.F_min
                true_solve = X.true_solve
                all_it = X.all_it
        X.true_solve = true_solve
        X.F_min = F_min
        X.all_it = all_it
    else:
        X.iterate_seq()
    X.show_info()

    if 'time' in sys.argv:
        print(f'ended in {time.time() - duration}\n')


def parall_mode(P_COUNT):
    random.seed(P_COUNT)
    duration = time.time()
    X = SolveX()

    # общие переменные
    F_min = Value('d', sum(X.data_exchange.values()) / 2)
    true_solve = Array('i', [-1 for _ in range(X.N)])
    q = Queue(maxsize=1)

    p = [Process(target=get_best, args=(true_solve, F_min, q)) for _ in range(P_COUNT)]

    for proc in p:
        proc.start()
    for proc in p:
        proc.join()

    if F_min.value == sum(X.data_exchange.values()) / 2:
        print('failure', sep='\n')
    else:
        print('success',
              f'solve= {true_solve[:]}',
              f'intensity= {F_min.value}',
              sep='\n'
        )
        print(f'max_intensity= {sum(X.data_exchange.values()) / 2}')
        if 'proc_load' in sys.argv:
            t = [0 for _ in range(X.M)]
            for i, x in enumerate(true_solve[:]):
                t[x - 1] += X.N_load[i]
            t = [t[i] / X.M_max_load[i] * 100 for i in range(X.M)]
            print(f'percent of load proc= {t}')
    if 'time' in sys.argv:
        print(f'ended in {time.time() - duration}\n')


class InputError(Exception):
    pass


if __name__ == '__main__':
    try:
        if 'seq' in sys.argv:
            seq_mode()
        elif 'parall' in sys.argv:
            N = sys.argv[sys.argv.index('parall') + 1]
            parall_mode(int(N))
        elif 'compare' in sys.argv:
            N = int(sys.argv[sys.argv.index('compare') + 1])
            seq_mode(N)
            print()
            parall_mode(int(N))
    except InputError:
        print('error in input_file')





