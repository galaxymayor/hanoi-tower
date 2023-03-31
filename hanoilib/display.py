'''The module contains the class Show to show the tower'''
from dataclasses import dataclass
from typing import Literal
from colorama import Back, Cursor
from . import HenoiStepOver, Plate, Position, Tower, Movement
from ._show import Lines, FutureMoves, TowerInfo,\
    draw_tower_from_given_repr, _add_border, evaluate, eval_to_lines, draw_plate, draw_piller

CSI = '\033['


@dataclass(slots=True)
class ShowConfiguration:
    '''The class contains configurations to show the tower'''
    eval: bool = False
    border: bool = True
    piller_color: str = ''
    border_color: str = Back.GREEN
    plate_color: str = ''
    width: Literal['auto', 'half', 'full'] = 'auto'
    show_plate_level: bool = False
    spliter: str = ' '


@dataclass(slots=True)
class Edit:
    '''The class save a change'''
    zone: Literal['t', 'e']
    row: int | None
    col: int | None
    new: tuple[Movement, bool | None] | Plate | None = None


class Show:
    '''The class contains configurations and methods to save shown tower string and\
        can evaluate how to use ANSI Cursor to modify the output to fix the next change'''
    evaluations: FutureMoves
    config: ShowConfiguration
    __tower: Tower
    editions: list[Edit]
    plate_repr: list[str]

    def __init__(self, tower: Tower, configuration: ShowConfiguration) -> None:
        self.__tower = tower
        self.evaluations = evaluate(tower, len(tower.plates_pos))
        self.config = configuration
        self.editions = []

    @property
    def tower_length(self) -> int:
        '''Get the length of the tower'''
        return len(self.__tower.plates_pos)

    def get_stack_len(self, pos: Position) -> int:
        '''Get the length of the stack at the position'''
        return len(self.__tower[pos])

    @property
    def display_lines(self) -> Lines:
        '''Get the lines to display'''

        if self.config.eval:
            lines = Lines(f'{self.config.border_color}  {Back.RESET}'.join(line)
                          for line in zip(self.tower_lines, self.evaluation_lines))
            lines.set_width(self.tower_lines.width()+2 +
                            self.evaluation_lines.width())
        else:
            lines = self.tower_lines
        line_width = lines.width()
        if self.config.border:
            lines = Lines(_add_border(
                lines, ' ', '  ',
                border_color=self.config.border_color,
                content_width=lines.width()
            ))
            lines.set_width(line_width+4)
        return lines

    @property
    def tower_lines(self) -> Lines:
        '''Get the lines to display the tower'''
        cfg = self.config
        info = TowerInfo.eval_tower_info(self.__tower, cfg.width)
        self.generate_repr()
        return draw_tower_from_given_repr(
            self.__tower,
            self.plate_repr,
            info.unit_width,
            cfg.border_color+cfg.spliter*(3*info.unit_width),)

    @property
    def evaluation_lines(self) -> Lines:
        '''Get the lines to display the evaluation'''
        evaluate_lines = eval_to_lines(
            self.evaluations.known,
            self.evaluations.unknown is None,
            fix_steps=self.tower_length)
        evaluate_lines.append(
            f'{self.config.border_color}{" "*14}{Back.RESET}')
        evaluate_lines.append('  next steps  ')
        return evaluate_lines

    def __str__(self) -> str:
        return '\n'.join(self.display_lines)

    def move(self, movement: Movement) -> None:
        '''Move a plate in the tower'''
        self.edit_tower(movement)
        self.edit_evaluation(movement)
        self.__tower.move(movement)

    def next(self) -> None:
        '''Move to the next step'''
        if not self.config.eval:
            try:
                next_step = next(self.evaluations)
                self.edit_tower(next_step)
                self.__tower.move(next_step)
                return
            except StopIteration as exc:
                raise HenoiStepOver from exc
        if self.evaluations.calculate_till(1):
            self.move(self.evaluations.known[0])
        else:
            self.editions.append(Edit('e', 0, None, None))
            raise HenoiStepOver

    def read_editions(self) -> str:
        '''Read the editions'''
        resault = ''.join(self.decode_edition(edit) for edit in self.editions)
        self.editions.clear()
        return f'\033[s{resault}\x1b[0m\033[u'

    def edit_tower(self, move: Movement) -> None:
        '''Add an edition'''
        edit = self.editions.append
        fr_row, to_row = map(lambda p: self.tower_length-self.get_stack_len(p),
                             move)
        edit(Edit('t', fr_row, move[0], None))
        edit(Edit('t', to_row-1, move[1], self.__tower[move[0]][-1]))

    def edit_evaluation(self, move: Movement) -> None:
        '''Add an edition to the evaluation part'''
        try:
            next_eval = next(self.evaluations)
        except StopIteration:
            self.evaluations.insert(move.reverse())
            if self.config.eval:
                self.editions.append(Edit('e', 0, None, (move.reverse(), True)))
            return
        edit = self.editions.append
        state: Literal[0, 1, 2]  # 0 for same, 1 for unnecessary, 2 for other
        if move == next_eval:
            state = 0
        elif move[0] == next_eval[0]:
            self.evaluations.insert(Movement(move[1], next_eval[1]))
            state = 1
        else:
            self.evaluations.known.clear()
            self.evaluations.unknown = self.__tower.move(move).eval()
            self.__tower.move(move.reverse())
            state = 2

        if not self.config.eval:
            return

        ev_len = self.evaluations.calculate_till(self.tower_length+1)

        if not ev_len:
            edit(Edit('e', 0, None, None))
            return

        if ev_len == 1:
            edit(Edit('e', 0, None, (self.evaluations.known[0], True)))
            edit(Edit('e', None, None, None))
            return

        edit(Edit('e', 0, None, (self.evaluations.known[0], None)))
        if state != 1:
            end = ev_len <= self.tower_length
            till = min(ev_len, self.tower_length)-1
            for ev_move in self.evaluations.known[1:till]:
                edit(Edit('e', None, None, (ev_move, None)))
            edit(Edit('e', None, None, (self.evaluations.known[till], end)))
            if end and ev_len < self.tower_length:
                edit(Edit('e', None, None, None))

    def decode_edition(self, edit: Edit) -> str:
        '''Decode the change'''
        if edit.zone == 't':
            return self._decode_tower_edition(edit)
        return self._decode_evaluation_edition(edit)

    def _decode_tower_edition(self, edit: Edit) -> str:
        '''Decode a tower edition'''
        match edit:
            case Edit(_, int(row), int(col), value):
                # assert isinstance(value, Plate) or value is None
                unit_width = self.tower_lines.width()//3
                padx = self.config.border*2
                pady = self.config.border
                x_pos = col*unit_width+padx
                y_pos = row+pady

                if value is None:
                    value = self.plate_repr[0]
                else:
                    value = self.plate_repr[value] # type: ignore
            case _:
                raise ValueError('Invalid edit')

        return f'{Cursor.POS(x_pos+1, y_pos+1)}{value}'

    def _decode_evaluation_edition(self, edit: Edit) -> str:
        '''Decode an evaluation edition'''
        match edit:
            case Edit(_, row, None, tuple((move, end))):
                value = f'  {move}{" "*6 if end is None else " @    " if end else " ...  "}'
            case Edit(_, row, None, None):
                value = ' '*14
            case _:
                raise ValueError('Invalid edit')
        padx = self.config.border*2
        pady = self.config.border
        pos_str = \
            Cursor.POS(self.tower_lines.width()+padx*2+1,
                       row+pady+1) if row is not None else Cursor.DOWN(1)+Cursor.BACK(14)
        return f'{pos_str}{value}'

    def generate_repr(self) -> None:
        '''Generate the representation of the tower'''
        cfg = self.config
        info = TowerInfo.eval_tower_info(self.__tower, cfg.width)
        self.plate_repr = [draw_plate(
            plate, info.unit_width, info.half,
            show_plate_level=cfg.show_plate_level,
            plate_color=cfg.plate_color)
            for plate in range(1, self.tower_length+1)]
        self.plate_repr.insert(0, draw_piller(
            info.unit_width, info.half, piller_color=cfg.piller_color))
