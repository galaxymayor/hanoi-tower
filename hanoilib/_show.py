'''This module halps you format a Tower'''
from collections import deque
from dataclasses import dataclass
from itertools import chain
from typing import Iterable, Iterator, Literal
# from typing_extensions import deprecated
from colorama import Back, init
from . import HenoiStepOver, MoveGen, Plate, Stack, Tower, Movement

init(autoreset=True)


class TowerInfo(tuple[int, int, bool]):
    '''A tuple of (height, unit width, half)'''
    height: int
    unit_width: int
    half: bool

    def __new__(cls, height: int, unit_width: int, half: bool):
        return super().__new__(cls, (height, unit_width, half))

    def __getattribute__(self, __name: str):
        if __name == 'height':
            return self[0]
        if __name == 'unit_width':
            return self[1]
        if __name == 'half':
            return self[2]
        return super().__getattribute__(__name)

    @staticmethod
    def eval_tower_info(tower: Tower, mode: Literal['auto', 'full', 'half'] = 'auto'):
        '''Get the information of a tower'''
        height = len(tower.plates_pos)
        half = half_tower(mode, height)
        name_width = max(len(tower.start.name), len(
            tower.temp.name), len(tower.end.name))+2
        unit_width = max(name_width, height) if half else max(
            name_width, height*2-1)
        return TowerInfo(height, unit_width+2, half)


class Lines(list[str]):
    '''A list of lines'''
    _width: int | None = None

    def __add__(self, other: list[str]) -> 'Lines':
        return Lines(chain(self, other))

    def width(self) -> int:
        '''Get the length of a line'''
        return len(self[0]) if self._width is None else self._width

    def set_width(self, length: int) -> None:
        '''Set the length of a line'''
        self._width = length


@dataclass(slots=True)
class FutureMoves:
    '''A tuple of known Movements and a generator of unknown Movements'''
    known: deque[Movement]
    unknown: MoveGen | None

    def __init__(self, known: deque[Movement], unknown: MoveGen | None) -> None:
        self.known = known
        self.unknown = unknown

    def insert(self, move: Movement) -> None:
        '''Insert a Movement'''
        self.known.insert(0, move)

    def calculate_one(self) -> None:
        '''Calculate one Movement'''
        if self.unknown is None:
            return
        try:
            self.known.append(next(self.unknown))
        except StopIteration:
            self.unknown = None

    def calculate_till(self, steps: int) -> int:
        '''Calculate Movements till steps'''
        if self.unknown is None:
            return len(self.known)
        try:
            for _ in range(max(0, steps-len(self.known))):
                self.known.append(next(self.unknown))
        except StopIteration:
            self.unknown = None
        finally:
            return len(self.known)

    def calculate_all(self) -> None:
        '''Calculate the unknown Movements'''
        if self.unknown is None:
            return
        for move in self.unknown:
            self.known.append(move)
        self.unknown = None

    def __next__(self) -> Movement:
        '''Read the first Movement'''
        if self.known:
            return self.known.popleft()
        if not self.unknown:
            raise StopIteration
        try:
            return next(self.unknown)
        except StopIteration as exc:
            self.unknown = None
            raise StopIteration from exc

    def reader(self) -> MoveGen:
        '''Read the Movements'''
        known, unknown = self.known, self.unknown
        for _ in range(len(known)):
            yield known.popleft()
        if unknown is not None:
            yield from unknown

    def __iter__(self) -> Iterator[Movement]:
        '''Iterate the Movements'''
        return self

    def __bool__(self) -> bool:
        '''Check if there is a Movement'''
        if not self.known:
            if self.unknown is None:
                return False
            try:
                self.known.append(next(self.unknown))
            except StopIteration:
                self.unknown = None
                return False
        return True


def show(tower: Tower, width: Literal['half', 'full', 'auto'] = 'auto', *,
         show_plate_level: bool = False, evaluation: bool = False, bd: bool = False,
         border_color: str = Back.GREEN, piller_color: str = '', plate_color: str = '') -> str:
    '''Show a tower'''

    lines = draw_tower(tower, width, show_plate_level=show_plate_level, spliter=' ',
                       spliter_color=border_color,
                       piller_color=piller_color,
                       plate_color=plate_color)
    tower_width = lines.width()

    if evaluation:
        evaluations = show_evaluation(
            tower, spliter=' ', spliter_color=border_color)[0]
        lines = Lines(f'{border_color}  {Back.RESET}'.join(line)
                      for line in zip(lines, evaluations))
        lines.set_width(tower_width+2+evaluations.width())

    if bd:
        lines = _add_border(lines, ' ', '  ',
                            border_color=border_color,
                            content_width=lines.width())

    return '\n'.join(lines)


# Unit tower


def draw_tower_from_given_repr(
        tower: Tower, reprs: list[str], unit_width: int, spliter: str) -> Lines:
    '''Draw a tower from a given representation'''
    length = len(tower.plates_pos)
    drawn_tower = (draw_stack_from_given_repr(stack, reprs, length, unit_width)
                   for stack in (tower.start, tower.temp, tower.end))
    lines = add_names(
        Lines(''.join(ss) for ss in zip(*drawn_tower)),
        (tower.start.name, tower.temp.name, tower.end.name),
        unit_width,
        spliter
    )
    lines.set_width(unit_width*3)
    return lines


def draw_tower(
    tower: Tower, width: Literal['half', 'full', 'auto'] = 'auto', *,
    show_plate_level: bool = False,
    spliter: str = '=', spliter_color: str = '',
    piller_color: str = '', plate_color: str = ''
) -> Lines:
    '''Draw a tower'''
    tower_info = TowerInfo.eval_tower_info(tower, width)

    drawn_tower = (draw_stack(stack, tower_info,
                              show_plate_level=show_plate_level,
                              piller_color=piller_color,
                              plate_color=plate_color)
                   for stack in (tower.start, tower.temp, tower.end))

    lines = add_names(
        Lines(''.join(line) for line in zip(*drawn_tower)),
        (tower.start.name, tower.temp.name, tower.end.name),
        tower_info[1],
        spliter=spliter_color+spliter*(3*tower_info[1])
    )
    lines.set_width(tower_info[1]*3)
    return lines


# Unit evaluation

def evaluate(tower: Tower, steps: int) -> FutureMoves:
    '''Return evaluastion to the steps, and the rest generator'''
    resault: deque[Movement] = deque()
    add_known = resault.append

    try:
        eval_gen = tower.eval()
        for _ in range(steps):
            add_known(next(eval_gen))
    except (StopIteration, HenoiStepOver):
        return FutureMoves(resault, None)

    return FutureMoves(resault, eval_gen)


def eval_to_lines(
    evaluations: list[Movement] | deque[Movement], done: bool = False, *,
    fix_steps: int | None = None,
    left_wrap: str = ' '*2, right_wrap: str = ' '*6,
    unfinish: str = ' ...  ', finish: str = ' @    '
) -> Lines:
    '''Convert a list of Movement to a Lines and a generator of next evaluations'''
    if not evaluations:
        return Lines([' '*(len(left_wrap+right_wrap)+6)]*(fix_steps or 0))
    resault = Lines(
        str(m).join((left_wrap, right_wrap)) for m, _ in zip(evaluations, range((fix_steps or 1)-1))
    )
    resault.append(
        f'{left_wrap}{evaluations[-1]}{finish if done else unfinish}')
    if fix_steps is not None:
        resault.extend([' '*len(resault[0])]*(fix_steps-len(evaluations)))
    return resault


def show_evaluation(
    tower: Tower, steps: int | None = None, *,
    spliter: str = '=', spliter_color=''
) -> tuple[Lines, FutureMoves]:
    '''Show the evaluation of a tower'''
    if steps is None:
        steps = len(tower.plates_pos)
    unit_width = 14

    evaluation = evaluate(tower, steps+1)
    done = not evaluation
    known = list(evaluation.known)
    # eval_gen = evaluation.unknown
    # if eval_gen is None:
    #     done = True
    #     next_eval = []
    # else:
    #     done = False
    #     next_eval = known[-1:]
    resault = eval_to_lines(known[:min(len(known), steps)],
                            done=done, fix_steps=steps)
    resault.set_width(unit_width)
    add_line = resault.append
    add_line(spliter_color+spliter*unit_width)
    add_line('  next steps  ')

    return resault, evaluation

# Unit single plate


ANSI_RESET = '\x1b[39m\x1b[49m'


def draw_plate(
    plate: Plate | int, width: int, half: bool, *,
    show_plate_level: bool = False,
    plate_color: str = ''
) -> str:
    '''Draw a plate'''
    res = f'{plate if show_plate_level else "+":->{plate}}'
    if half:
        res = f'{res: >{width}}'
    else:
        res = f'{res}{"-"*(plate-1)}'.center(width)
    if plate_color:
        return f'{plate_color}{res}{ANSI_RESET}'
    return res


# Unit single stack

def draw_stack(
    stack: Stack, info: TowerInfo, *,
    piller_color: str = '', plate_color: str = '',
    show_plate_level: bool = False
) -> Lines:
    '''Draw a stack'''

    resault = Lines(chain(
        [draw_piller(
            info[1], info[2], piller_color=piller_color)] * (info[0]-len(stack)),
        (draw_plate(plate, info[1], info[2],
                    plate_color=plate_color,
                    show_plate_level=show_plate_level)
         for plate in reversed(stack))
    ))
    resault.set_width(info[1])

    return resault


def draw_stack_from_given_repr(
        stack: Stack, reprs: list[str], length: int | None, width: int) -> Lines:
    '''Draw a stack from a given representation'''
    if length is None:
        length = len(stack)
    resault = Lines(chain(
        [reprs[0]]*(length-len(stack)),
        (reprs[plate] for plate in reversed(stack))
    ))
    resault.set_width(width)

    return resault
# PART helper


def draw_piller(
    width: int, half: bool, *, piller_color: str = ''
) -> str:
    '''Draw a piller'''
    piller = f'{piller_color}|{ANSI_RESET}' if piller_color else '|'
    return piller.rjust(width) if half else piller.center(width)


def _add_border(
    lines: list[str],
    border_x_char: str = '#',
    border_y_str: str = '#', *,
    border_color: str = '\x1b[37m\x1b[40m',
    content_color: str = '\x1b[39m\x1b[49m',
    content_width: int | None = None,
) -> list[str]:
    if content_width is None:
        content_width = len(lines[0])
    border_x = border_color+border_x_char*(content_width+2*len(border_y_str))
    lines = [
        border_x,
        *[content.join((border_y_str+content_color, border_color+border_y_str))
          for content in lines],
        border_x
    ]
    return lines


def repeat_to_length(string: str, /, length: int) -> str:
    '''Repeat a string to a given length'''
    return (string * (length//len(string) + 1))[:length]


def half_tower(mode: Literal['auto', 'full', 'half'], length: int) -> bool:
    '''Decide if the tower should be half or full'''
    if mode == 'half':
        return True
    if mode == 'full':
        return False
    return length > 10


def add_names(original: Lines, names: Iterable[str], unit_width: int, spliter: str) -> Lines:
    '''Add names to a Lines'''
    resault, width = Lines(original), original.width()
    resault.append(spliter)
    resault.append(''.join(f'{name:^{unit_width}}' for name in names))
    resault.set_width(width)
    return resault


# PART deprecated

# @deprecated('Use draw_stack instead')
def __half_tower(
    tower: Tower,
    tower_width: int,
    side: Literal['left', 'right'] = 'left') -> tuple[
        list[tuple[str, Plate]],
        list[tuple[str, Plate]],
        list[tuple[str, Plate]]]:
    format_str = f'{"{: "}{">" if side=="left" else "<"}{tower_width}{"}"}'
    stack_a = [(format_str.format('-'*(w-1)), w)
               for w in reversed(tower.start)]
    stack_b = [(format_str.format('-'*(w-1)), w)
               for w in reversed(tower.temp)]
    stack_c = [(format_str.format('-'*(w-1)), w)
               for w in reversed(tower.end)]
    return stack_a, stack_b, stack_c


# @deprecated('Use draw_stack instead')
def __finish_tower(
    semi_tower: tuple[list[tuple[str, Plate]], list[tuple[str, Plate]], list[tuple[str, Plate]]],
    width: int,
    height: int | None, *,
    duplicate: bool = False,
    show_plate_level: bool = False,
    piller_color: str = '',
    plate_color: str = '',
) -> tuple[list[str], list[str], list[str]]:
    empty_str = ' '*width
    piller = '|'.join((piller_color, '\x1b[39m\x1b[49m'))
    plate_wrap = (plate_color, '\x1b[39m\x1b[49m')
    lengthes = map(len, semi_tower)
    if height is None:
        height = sum(lengthes)
    return tuple(
        __finish_stack((stack, length), height, empty_str,
                       show_plate_level=show_plate_level,
                       duplicate=duplicate,
                       piller=piller,
                       plate_wrap=plate_wrap)
        for stack, length in zip(semi_tower, lengthes))


# @deprecated('Use draw_stack instead')
def __finish_stack(
    unfinished_stack_and_length: tuple[list[tuple[str, Plate]], int],
    height: int,
    half_empty_str: str, *,
    show_plate_level: bool = False,
    duplicate: bool = False,
    piller: str = '|',
    plate_wrap: tuple[str, str] = ('', '')
) -> list[str]:
    unfinished_stack, length = unfinished_stack_and_length
    return [
        piller.join((half_empty_str, half_empty_str if duplicate else ' '))
    ]*(height-length)+[
        (center := (str(l) if show_plate_level else '+')).join(
            (left[: till if (till := -len(center)+1) else None],
             left[::-1] if duplicate else ' ')
        ).join(plate_wrap)
        for left, l in unfinished_stack
    ]

# end
