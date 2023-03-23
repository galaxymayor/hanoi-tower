'''This module halps you format a Tower'''
from itertools import chain
from typing import Literal
from colorama import Back, init
from . import HenoiStepOver, Plate, Tower, Movement

init(autoreset=True)


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


def draw_tower(tower: Tower, width: Literal['half', 'full', 'auto'] = 'auto', *,
               show_plate_level: bool = False,
               spliter: str = '=', spliter_color: str = '',
               piller_color: str = '', plate_color: str = '') -> Lines:
    '''Draw a tower'''
    tower_high = len(tower.plates_pos)
    match width:
        case 'half':
            double_unit = False
        case 'full':
            double_unit = True
        case 'auto':
            double_unit = tower_high < 11
    name_width = max(len(tower.start.name), len(
        tower.temp.name), len(tower.end.name))+2
    unit_width = max(name_width//2, tower_high) if double_unit else \
        max(name_width, tower_high)

    stack_a_l, stack_b_l, stack_c_l = _finish_tower(
        half_tower=_half_tower(tower, unit_width),
        width=unit_width,
        height=tower_high,
        duplicate=double_unit,
        show_plate_level=show_plate_level,
        piller_color=piller_color,
        plate_color=plate_color
    )

    unit_width = unit_width*2+1 if double_unit else unit_width+2
    name = (tower.start.name.join('[]').center(unit_width),
            tower.temp.name.join('[]').center(unit_width),
            tower.end.name.join('[]').center(unit_width))

    lines = Lines(
        ''.join(line) for line in
        chain(zip(stack_a_l, stack_b_l, stack_c_l),
              (spliter_color+spliter*(3*unit_width), ),
              (name, ))
    )
    lines.set_width(unit_width*3)
    return lines


def show_evaluation(tower: Tower, steps: int | None = None, *,
                    spliter: str = '=', spliter_color='') -> tuple[Lines, Movement | None]:
    '''Show the evaluation of a tower'''
    if steps is None:
        steps = len(tower.plates_pos)
    unit_width = 14
    right_space = ' '*6
    left_space = ' '*2

    resault = Lines()
    resault.set_width(unit_width)
    add_line = resault.append
    try:
        eval_gen = tower.eval()
    except HenoiStepOver:
        resault.extend([
            *[' '*unit_width]*steps,
            spliter_color+spliter*unit_width,
            '  next steps  '
        ])
        return resault, None
    this_eval = next(eval_gen)

    for index in range(steps-1):
        try:
            next_eval = next(eval_gen)
        except StopIteration:
            add_line(str(this_eval).join((left_space, ' @    ')))
            resault.extend([' '*unit_width]*(steps-index-1))
            add_line(spliter_color+spliter*unit_width)
            add_line('  next steps  ')
            return resault, None
        add_line(str(this_eval).join((left_space, right_space)))
        this_eval = next_eval

    try:
        next_eval = next(eval_gen)
    except StopIteration:
        add_line(str(this_eval).join((left_space, ' @    ')))
        next_eval = None
    else:
        add_line(str(this_eval).join((left_space, ' ...  ')))

    add_line(spliter_color+spliter*unit_width)
    add_line('  next steps  ')

    return resault, next_eval


# PART helper

def _half_tower(
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


def _finish_tower(
    half_tower: tuple[list[tuple[str, Plate]], list[tuple[str, Plate]], list[tuple[str, Plate]]],
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
    lengthes = map(len, half_tower)
    if height is None:
        height = sum(lengthes)
    return tuple(
        _finish_stack((stack, length), height, empty_str,
                      show_plate_level=show_plate_level,
                      duplicate=duplicate,
                      piller=piller,
                      plate_wrap=plate_wrap)
        for stack, length in zip(half_tower, lengthes))


def _finish_stack(
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

# end
