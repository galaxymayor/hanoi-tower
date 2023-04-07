'''Functions, exceptions and classes of henoi tower'''

# PART import

from collections import deque
from dataclasses import dataclass, field
from typing import Generator, Iterable, Iterator, Literal, Protocol, Self, Type, overload


# PART exception


class HenoiImposible(ValueError):
    '''imposible situation'''


class HenoiOrderFail(HenoiImposible):
    '''The order should be consecutively decreasing'''


class HenoiStepOver(HenoiImposible):
    '''over than all step'''


class HenoiPositionError(HenoiImposible):
    '''Positions are only a, b or c'''


# PART main class

Position = Literal[0, 1, 2]

PositionChar = Literal['a', 'b', 'c']


class Pos:
    '''Contains function having to do with Position'''
    @staticmethod
    def _from_chr(p: PositionChar, /) -> Position:
        return ord(p)-97  # type: ignore
        # ord('a') = 97

    @staticmethod
    def _to_chr(p: Position, /) -> PositionChar:
        return chr(p+97)  # type: ignore

    @staticmethod
    def from_chr(p: PositionChar | str, /) -> Position:
        '''a -> 0, b -> 1, c -> 2'''
        resault = ord(p)-97
        if resault not in {0, 1, 2}:
            raise HenoiPositionError('only a b c is valid')
        return resault  # type: ignore

    @staticmethod
    def to_chr(p: Position | int, /) -> PositionChar:
        '''0 -> a, 1 -> b, 2 -> c'''
        resault = chr(p+97)
        if resault not in {'a', 'b', 'c'}:
            raise HenoiPositionError('only 0, 1, 2 is valid')
        return resault  # type: ignore

# Plate = int


class Plate(int):
    '''A henoi plate'''

    def __new__(cls: type[Self], *args, **kwargs) -> Self:
        self = int(*args, **kwargs)
        if self < 1:
            raise HenoiOrderFail('plate should > 0')
        return super().__new__(cls, self)


class Stack(deque[Plate]):
    '''A Stack is a container of Plate'''
    name: str

    _position: Position = field(init=False)

    def __init__(self, plates: Iterable[Plate] | None = None,
                 name: str = '', maxlen: int | None = None) -> None:
        plates = plates or []
        Stack._check(plates)
        super().__init__(plates, maxlen=maxlen)
        self.name = name

    @staticmethod
    def _check(plates: Iterable[Plate]) -> None:
        if not plates:
            return
        # if any(a <= b for a, b in zip(plates, plates[1:])):
        #     raise HenoiOrderFail('plates should be consecutively decreasing.')
        iterator = iter(plates)
        prev_item = next(iterator)
        for item in iterator:
            if item >= prev_item:
                raise HenoiOrderFail(
                    'plates should be consecutively decreasing.')
            prev_item = item

    def push(self, plate: Plate) -> None:
        '''push a plate to back.'''
        if self and plate >= self[-1]:
            raise HenoiOrderFail(f'{plate} >= {self[-1]}')
        self.append(plate)

    def copy(self) -> Self:
        '''copy a stack'''
        return self.__class__(self, self.name)

    def __repr__(self) -> str:
        return f'<{self.name} : {super().__repr__()}>'


class StackStart(Stack):
    '''Stack in start (Position a)'''
    name = 'start'
    _position = 0


class StackTemp(Stack):
    '''Stack in middle (Position b)'''
    name = 'temporary'
    _position = 1


class StackEnd(Stack):
    '''Stack in the end (Position c)'''
    name = 'end'
    _position = 2


class Movement(tuple[Position, Position]):
    '''Movement: which stack is poped, which is pushed'''

    def __new__(cls: type[Self], from_: Position, to: Position) -> Self:
        return super().__new__(cls, (from_, to))

    def __repr__(self) -> str:
        return f'{Pos._to_chr(self[0])} -> {Pos._to_chr(self[1])}'

    def reverse(self) -> Self:
        '''opposite directed movement'''
        return Movement(self[1], self[0])

    @staticmethod
    def eval(step: int, level: int, *,
             start_pos: Position = 0, end_pos: Position = 2) -> 'Movement':
        '''the function solve a henoi move on the step. odd level are diffrent direction to eve.'''
        step_posible(step, level)
        return _move(step, level, start_pos=start_pos, end_pos=end_pos)

    @staticmethod
    def from_str(_s: str) -> 'Movement':
        '''match string into a Movement, e.g. 'a -> c' will be Movement('a', 'c') '''
        try:
            return Movement(*map(Pos.from_chr, _s.split(' -> ')))
        except ValueError as exc:
            raise HenoiImposible('no such movement') from exc


class Positions(Protocol):
    '''a list of Position'''
    @overload
    def __getitem__(self, index: int) -> Position: ...
    @overload
    def __getitem__(self, index: slice) -> Self: ...
    def __setitem__(self, index: int, value: Position) -> None: ...
    def __iter__(self) -> Iterator[Position]: ...
    def __len__(self) -> int: ...

    def append(self, __obj: Position) -> None:
        '''Add item into the end'''


@dataclass(slots=True)
class Tower:
    # pylint: disable=protected-access
    '''A Tower contains three henoi stacks.'''
    _stacks: tuple[Stack, Stack, Stack] = field(init=False)
    start: StackStart = field(default_factory=StackStart)
    temp: StackTemp = field(default_factory=StackTemp)
    end: StackEnd = field(default_factory=StackEnd)
    name: str = ''
    plates_pos: Positions = field(init=False)

    def __post_init__(self) -> None:
        self._stacks = (self.start, self.temp, self.end)
        self.update_plates_pos()

    def update_plates_pos(self) -> None:
        '''update the plates_pos'''
        pos_l = bytearray(b'\x80') * \
            (len(self.start)+len(self.temp)+len(self.end))
        try:
            for plate in self.start:
                # assert pos_l[-plate] == 128
                pos_l[-plate] = 0
            for plate in self.temp:
                # assert pos_l[-plate] == 128
                pos_l[-plate] = 1
            for plate in self.end:
                # assert pos_l[-plate] == 128
                pos_l[-plate] = 2
        except KeyError as exc:
            raise HenoiOrderFail('Not consecutive') from exc
        except AssertionError as exc:
            raise HenoiOrderFail('Same order') from exc
        self.plates_pos = pos_l  # type: ignore

    def move(self, movement: Movement) -> Self:
        '''Move a plate, if possible'''
        stack_fr = self[movement[0]]
        stack_to = self[movement[1]]
        plate = stack_fr.pop()
        try:
            stack_to.push(plate)
        except HenoiOrderFail as error:
            stack_fr.push(plate)
            raise HenoiOrderFail from error
        self.plates_pos[-plate] = movement[1]
        return self

    def _move_without_check(self, movement: Movement) -> None:
        self[movement[1]].append(plate := self[movement[0]].pop())
        self.plates_pos[-plate] = movement[1]

    def eval(self) -> 'MoveGen':
        '''eviluate next steps'''
        tower_tall = len(self.start)+len(self.temp)+len(self.end)
        for order, pos in enumerate(self.plates_pos):
            if pos != 2:
                index = order
                want_p = 2
                break
        else:
            raise HenoiStepOver('finish')
        if all((a == b) for a, b in zip(self.plates_pos, self.plates_pos[1:])):
            return _moves(tower_tall, start_pos=self.plates_pos[0], end_pos=2)
        move_list: list[Movement] = []
        add_move = move_list.append
        for order, pos in enumerate(self.plates_pos[index:], start=index):
            if ((not self[want_p]) or
                    ((tower_tall - order) < self[want_p][-1])
                ) \
                    and (tower_tall - order) == self[pos][-1]:
                add_move(Movement(pos, want_p))
                break
            add_move(Movement(pos, want_p))
            if (anthor := _other(pos, want_p)) is not None:
                want_p = anthor
        move_list.reverse()
        return _stepfy(move_list, tower_tall, index)

    # def show_dot(self) -> str:
    #     high = max(len(self.start), len(self.temp), len(self.end))

    def copy(self) -> Self:
        '''copy self'''
        return Tower(
            self.start.copy(),
            self.temp.copy(),
            self.end.copy(),
            name=self.name
        )

    def __add__(self, movement: Movement) -> Self:
        return self.copy().move(movement)

    def __repr__(self) -> str:
        return str.join('', map(Pos._to_chr, self.plates_pos))

    def __getitem__(self, p: Position, /) -> Stack:
        '''return stack at the position'''
        return self._stacks[p]

    @staticmethod
    def new(step: int, level: int, *, start_pos: Position = 0, end_pos: Position = 2,
            tower_name: str = '',
            stack_names: tuple[str, str, str] = ('start', 'temporary', 'end')) -> 'Tower':
        '''create a tower.'''
        step_posible(step, level)
        return _new_tower(step, level, start_pos=start_pos, end_pos=end_pos,
                          tower_name=tower_name, stack_names=stack_names)


# PART helper


def match_stack_type(p: Position, /) -> Type[Stack]:
    '''return correct type of stack'''
    if p > 2:
        raise HenoiPositionError()
    return STACK_TYPES[p]


STACK_TYPES = (StackStart, StackTemp, StackEnd)

MOVES: tuple[tuple[Position, Position], ...] = (
    (0, 1), (2, 0), (1, 2)
)


REVERSE_B_C = (0, 2, 1)


def last_zero(i: int) -> int:
    '''Find out how many 1 are in back of the number. '''\
        '''For example, 0b101100111 |-> 3'''
    result = 0
    while i & 1:
        i >>= 1
        result += 1
    return result


def _other(a: Position, b: Position, /) -> Position | None:
    '''There are three Position: a, b and c. another(a, b)=c; another(c, a) = b ...'''
    if a == b:
        return None

    return (a | b) ^ 3  # type: ignore


def other(a: Position, b: Position, /) -> Position:
    '''There are three Position: a, b and c. another(a, b)=c; another(c, a) = b ...'''
    if a == b:
        raise HenoiPositionError()

    return (a | b) ^ 3  # type: ignore
    # 294=97+98+99 = ord('a')+ord('b')+ord('c')


def step_posible(step: int, level: int) -> bool:
    '''A henoi step should < 2**level'''
    return pow(2, level) > step


MoveGen = Generator[Movement, None, None]

bit_length = int.bit_length


def _stepfy(expected_moves: list[Movement],
            plate_quantity: int,
            start_index: int) -> MoveGen:
    top_level = plate_quantity-len(expected_moves)-start_index
    for index, move in enumerate(expected_moves, top_level):
        temp_pos, end_pos = move
        if temp_pos == end_pos:
            continue
        yield move

        start_pos: Position = (end_pos | temp_pos) ^ 3  # type: ignore
        if index & 1:
            temp_pos, end_pos = end_pos, temp_pos
        states = (
            Movement(start_pos, temp_pos),
            Movement(end_pos, start_pos),
            Movement(temp_pos, end_pos)
        )
        states_rev = (
            Movement(temp_pos, start_pos),
            Movement(start_pos, end_pos),
            Movement(end_pos, temp_pos)
        )
        for step in range((1 << index)-1):
            if bit_length(step+1 ^ step) & 1:  # right most 0 position is odd
                yield states[step % 3]
            else:
                yield states_rev[step % 3]


def _change_pos(a: Position, b: Position, c: Position, *positions: Position) -> list[Position]:
    # pylint: disable=invalid-name
    return [a if pos == 0 else b if pos == 1 else c for pos in positions]

# PART main func


def _move(step: int, level: int, *, start_pos: Position = 0, end_pos: Position = 2) -> Movement:
    '''the function solve a henoi move on the step. '''\
        '''odd level are diffrent direction to eve'''
    # pylint: disable=invalid-name
    temp_pos = (start_pos | end_pos) ^ 3
    step_state = step % 3
    if level & 1:
        temp_pos, end_pos = end_pos, temp_pos  # type: ignore
    if not step_state:
        from_, to = start_pos, temp_pos
    elif step_state & 1:
        from_, to = end_pos, start_pos
    else:
        from_, to = temp_pos, end_pos
    if not (step+1 ^ step).bit_length() & 1:  # right most 0 position is odd
        from_, to = to, from_
    return Movement(from_, to)  # type: ignore


def _moves(level: int, *, start_pos: Position = 0, end_pos: Position = 2) -> MoveGen:
    '''the function solve a henoi move on the step. '''\
        '''odd level are diffrent direction to eve'''
    # pylint: disable=invalid-name
    temp_pos: Position = (start_pos | end_pos) ^ 3  # type: ignore
    if level & 1:
        temp_pos, end_pos = end_pos, temp_pos
    states = (
        Movement(start_pos, temp_pos),
        Movement(end_pos, start_pos),
        Movement(temp_pos, end_pos)
    )
    states_rev = (
        Movement(temp_pos, start_pos),
        Movement(start_pos, end_pos),
        Movement(end_pos, temp_pos)
    )
    for step in range((1 << level)-1):
        if bit_length(step+1 ^ step) & 1:  # right most 0 position is odd
            yield states[step % 3]
        else:
            yield states_rev[step % 3]


# def _bin_moves(level: int) -> MoveGen:
#     '''the function solve a henoi move on the step. '''\
#         '''odd level are diffrent direction to eve'''
#     for step, nstep in enumerate(range(1, (1 << level))):
#         yield Movement((step & nstep) % 3, ((step | nstep)+1) % 3)


def _new_tower(step: int, level: int, *, start_pos: Position = 0, end_pos: Position = 2,
               tower_name: str = '', stack_names: tuple[str, str, str] = ('', '', '')) -> Tower:
    '''caculate the state of step where there are level plates.'''
    assert start_pos != end_pos
    from_: list[Plate] = []
    temp: list[Plate] = []
    end: list[Plate] = []
    a_add, b_add, c_add = from_.append, temp.append, end.append
    plates = [Plate(x) for x in range(level, 0, -1)]

    if step == 0:
        return Tower(StackStart(plates, stack_names[0], plates[0]),
                     StackTemp([], stack_names[1], plates[0]),
                     StackEnd([], stack_names[2], plates[0]),
                     tower_name)

    if level == 1:
        return Tower(StackStart([], stack_names[0], 1),
                     StackTemp([], stack_names[1], 1),
                     StackEnd(plates, stack_names[2], 1),
                     tower_name)

    step_str = f'{step:b}'.zfill(level+1)
    push_str: Positions = \
        bytearray((start_pos, end_pos)) if step_str[1] == '1' else \
        bytearray((end_pos, start_pos))  # type: ignore
    push = push_str.append
    sep = 1

    for order, char in list(enumerate(step_str))[2:]:
        last = step_str[order-1]
        if char == last:
            push(push_str[-1])
            sep += 1
        else:
            if sep % 2:
                push(other(push_str[-1], push_str[-sep-1]))
            else:
                push(push_str[-sep-1])
            sep = 1

    for char, plate in zip(push_str[1:], plates):
        if char == 0:
            a_add(plate)
        elif char == 1:
            b_add(plate)
        elif char == 2:
            c_add(plate)

    return Tower(StackStart(from_, stack_names[0], plates[0]),
                 StackTemp(temp, stack_names[1], plates[0]),
                 StackEnd(end, stack_names[2], plates[0]),
                 tower_name)


# PART test


def __test() -> None:
    '''Write test here'''
    state = _new_tower(0, 5)
    print(state)
    # state += Movement('b', 'c')
    # state += Movement(0, 2)
    # print(state)
    # for move in state.eval():
    #     print(move)
    #     state.move(move)
    for i in range(7):
        print(_move(i, 3, start_pos=2, end_pos=1))


if __name__ == '__main__':
    __test()


# end
