'''This module halps you format a Tower'''
from itertools import chain
from typing import Literal
from . import HenoiStepOver, Tower


def show(tower: Tower, width: Literal['half', 'full', 'auto'] = 'auto', *,
         show_plate_level: bool = False, evaluation: bool = False, bd: bool = False) -> str:
    '''Show a tower'''
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
    format_str = f'{"{: >"}{unit_width}{"}"}'
    empty_str = format_str.format('')
    stack_a_l = [(format_str.format('-'*(w-1)), w)
                 for w in reversed(tower.start)]
    stack_b_l = [(format_str.format('-'*(w-1)), w)
                 for w in reversed(tower.temp)]
    stack_c_l = [(format_str.format('-'*(w-1)), w)
                 for w in reversed(tower.end)]
    stack_a_l = [
        '|'.join((empty_str, empty_str if double_unit else ' '))
    ]*(tower_high-len(tower.start))+[
        (center := (str(l) if show_plate_level else '+')).join(
            (left[: till if (till := -len(center)+1) else None],
             left[::-1] if double_unit else ' ')
        )
        for left, l in stack_a_l
    ]
    stack_b_l = [
        '|'.join((empty_str, empty_str if double_unit else ' '))
    ]*(tower_high-len(tower.temp))+[
        (center := (str(l) if show_plate_level else '+')).join(
            (left[: till if (till := -len(center)+1) else None],
             left[::-1] if double_unit else ' ')
        )
        for left, l in stack_b_l
    ]
    stack_c_l = [
        '|'.join((empty_str, empty_str if double_unit else ' '))
    ]*(tower_high-len(tower.end))+[
        (center := (str(l) if show_plate_level else '+')).join(
            (left[: till if (till := -len(center)+1) else None],
             left[::-1] if double_unit else ' ')
        )
        for left, l in stack_c_l
    ]

    unit_width = unit_width*2+1 if double_unit else unit_width+2
    names = [
        tower.start.name.join('[]'),
        tower.temp.name.join('[]'),
        tower.end.name.join('[]')
    ]
    names = [
        name.join((' '*((spaces := unit_width-len(name)) //
                  2+(spaces % 2)), ' '*(spaces//2)))
        for name in names
    ]
    spliter = '='*unit_width

    resault = [
        ''.join(line) for line in
        chain(zip(stack_a_l, stack_b_l, stack_c_l), ([spliter]*3, ), (names, ))
    ]

    if evaluation:
        new_resault = []
        add_line = new_resault.append
        try:
            eval_gen = tower.eval()
        except HenoiStepOver:
            new_resault = [t_s+'!!              ' for t_s in resault[:-2]]+[
                resault[-2]+'!!==============',
                resault[-1]+'!!  next steps  '
            ]
        else:
            this_eval = next(eval_gen)
            for index, tower_str in enumerate(resault[:-3]):
                try:
                    next_eval = next(eval_gen)
                except StopIteration:
                    add_line('!!  '.join((tower_str, str(this_eval)+' @    ')))
                    for t_s in resault[index+1:-2]:
                        add_line(t_s+'!!              ')
                    break
                add_line('!!  '.join((tower_str, str(this_eval)+' '*6)))
                this_eval = next_eval
            else:
                try:
                    next_eval = next(eval_gen)
                except StopIteration:
                    add_line('!!  '.join((resault[-3], str(this_eval)+' @    ')))
                else:
                    add_line('!!  '.join((resault[-3], str(this_eval)+' ...  ')))
            add_line('!!=='.join((resault[-2], '='*12)))
            add_line('!!  '.join((resault[-1], 'next steps  ')))
        finally:
            resault = new_resault

    if bd:
        bd_x = ['#'*(unit_width*3+(18 if evaluation else 2))]
        resault = bd_x+[
            content.join(('#', '#')) for content in resault
        ]+bd_x

    return '\n'.join(resault)

# end
