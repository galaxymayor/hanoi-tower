from hanoilib._show import show
from hanoilib import Tower
# import time


# def last_zero0(i: int) -> int:
#     '''Find out how many 1 are in back of the number. '''\
#         '''For example, 0b101100111 |-> 3'''
#     result = 0
#     while i&1 :
#         i>>=1
#         result+=1
#     return result

# def last_zero1(i: int) -> int:
#     '''Find out how many 1 are in back of the number. '''\
#         '''For example, 0b101100111 |-> 3'''
#     result = -1
#     mod = 1
#     while mod:
#         i, mod = divmod(i, 2)
#         result += 1
#     return result


if __name__ == '__main__':
    # t0 = time.perf_counter()
    # for x in range(10_000_000):
    #     last_zero0(x)
    # t1 = time.perf_counter()
    # for x in range(10_000_000):
    #     last_zero1(x)
    # t2 = time.perf_counter()
    # print(t1-t0)
    # print(t2-t1)
    
    # print(last_zero0(1048575), last_zero1(1048575))
    print(
        show(Tower.new(23, 5), show_plate_level=True, evaluation=True, bd=True)
    )