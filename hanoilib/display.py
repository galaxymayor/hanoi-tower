'''The module contains the class Show to show the tower'''
from dataclasses import dataclass, field
from itertools import chain
from typing import Any, Callable, Literal
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


@dataclass(slots=True)
class TowerEdit(Edit):
    '''The class save a change in the tower'''
    zone: Literal['t'] = field(default='t', init=False)
    row: int
    col: int
    new: Plate | None = None


@dataclass(slots=True)
class EvalEdit(Edit):
    '''The class save a change in the evaluation'''
    zone: Literal['e'] = field(default='e', init=False)
    row: int | None = field(default=None, init=True)
    col: None = field(default=None, init=False)
    new: tuple[Movement, bool | None] | None = None


class Show:
    '''The class contains configurations and methods to save shown tower string and\
        can evaluate how to use ANSI Cursor to modify the output to fix the next change'''
    evaluations: FutureMoves
    config: ShowConfiguration
    __tower: Tower
    tower_editions: list[TowerEdit]
    eval_editions: list[EvalEdit]
    plate_repr: list[str]
    tower_info: TowerInfo

    def __init__(self, tower: Tower, configuration: ShowConfiguration) -> None:
        self.__tower = tower
        self.evaluations = evaluate(tower, len(tower.plates_pos))
        self.config = configuration
        self.tower_editions = []
        self.eval_editions = []
        self.tower_info = TowerInfo.eval_tower_info(tower, configuration.width)

    def get_stack_len(self, pos: Position) -> int:
        '''Get the length of the stack at the position'''
        return len(self.__tower[pos])

    @property
    def display_lines(self) -> Lines:
        '''Get the lines to display'''

        if self.config.eval:
            lines = Lines(f'{self.config.border_color}  {Back.RESET}'.join(line)
                          for line in zip(self.tower_lines, self.evaluation_lines))
            lines.set_width(self.tower_info.unit_width*3 + 2 + 14)
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
        info = self.tower_info = TowerInfo.eval_tower_info(
            self.__tower, cfg.width
        )
        self.generate_repr()
        self.tower_editions.clear()
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
            fix_steps=self.tower_info[0])
        evaluate_lines.append(
            f'{self.config.border_color}{" "*14}{Back.RESET}')
        evaluate_lines.append('  next steps  ')
        self.eval_editions.clear()
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
                self.__tower._move_without_check(next_step)
                return
            except StopIteration as exc:
                raise HenoiStepOver from exc
        if self.evaluations.calculate_till(1):
            self.move(self.evaluations.known[0])
        else:
            self.eval_editions.append(EvalEdit(0, None))
            raise HenoiStepOver

    def fast_play(self, io_cb: Callable[[str], Any]) -> None:
        '''Play the tower'''
        io_cb('\033[s')
        con = ''.join
        tower = self.__tower
        tower_st = tower._stacks
        poper = tower_st[0].pop, tower_st[1].pop, tower_st[2].pop
        adder = tower_st[0].append, tower_st[1].append, tower_st[2].append
        tower_h = self.tower_info[0]
        unit_w = self.tower_info[1]
        padx = (pady := self.config.border)*3
        piller = self.plate_repr[0]
        if self.tower_info[2]:
            pxsu = padx+unit_w
            plate_repr = tuple(x[-i:] for i, x in enumerate(self.plate_repr))
            piller_repr = tuple(piller[-i:] for i in range(tower_h+1))
        else:
            std_unit = unit_w//2
            pxsu = padx+std_unit+1
            plate_repr = tuple(x[std_unit-i+1:std_unit+i] for i, x in enumerate(self.plate_repr))
            piller_repr = tuple(piller[std_unit-i+1:std_unit+i] for i in range(tower_h+1))

        try:
            if not self.config.eval:
                th_fix_t = (th_fix_f := tower_h+pady)+1
                for p_fr, p_to in tower.eval():
                    plate = poper[p_fr]()
                    adder[p_to](plate)
                    io_cb(f'\
\033[{th_fix_f-len(tower_st[p_fr])};{p_fr*unit_w+pxsu-plate}f{piller_repr[plate]}\
\033[{th_fix_t-len(tower_st[p_to])};{p_to*unit_w+pxsu-plate}f{plate_repr[plate]}'
                    )
            else:
                for move in self.evaluations:
                    self.edit_tower(move)
                    self.edit_evaluation(move)
                    tower._move_without_check(move)
                    io_cb(con(chain(
                        (self._decode_tower_edition(edit)
                         for edit in self.tower_editions),
                        (self._decode_evaluation_edition(edit)
                         for edit in self.eval_editions)
                    )))
                    self.eval_editions.clear()
                    self.tower_editions.clear()
        finally:
            self.__tower.update_plates_pos()
            io_cb('\x1b[0m\033[u')
            # io_cb(None)

    def read_editions(self) -> str:
        '''Read the editions'''
        resault = f'''\033[s{"".join(chain(
            (self._decode_tower_edition(edit) for edit in self.tower_editions),
            (self._decode_evaluation_edition(edit) for edit in self.eval_editions),
        ))}\x1b[0m\033[u'''
        self.tower_editions.clear()
        self.eval_editions.clear()
        return resault

    def edit_tower(self, move: Movement) -> None:
        '''Add an edition'''
        edit = self.tower_editions.append
        fr_row, to_row = map(lambda p: self.tower_info[0]-self.get_stack_len(p),
                             move)
        edit(TowerEdit(fr_row, move[0], None))
        edit(TowerEdit(to_row-1, move[1], self.__tower[move[0]][-1]))

    def edit_evaluation(self, move: Movement) -> None:
        '''Add an edition to the evaluation part'''
        try:
            next_eval = next(self.evaluations)
        except StopIteration:
            self.evaluations.insert(move.reverse())
            if self.config.eval:
                self.eval_editions.append(EvalEdit(0, (move.reverse(), True)))
            return
        edit = self.eval_editions.append
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

        ev_len = self.evaluations.calculate_till(self.tower_info[0]+1)
        known = self.evaluations.known

        if not ev_len:
            edit(EvalEdit(0, None))
            return

        if ev_len == 1:
            edit(EvalEdit(0, (known[0], True)))
            edit(EvalEdit(None, None))
            return

        edit(EvalEdit(0, (known[0], None)))
        if state != 1:
            end = ev_len <= self.tower_info[0]
            till = min(ev_len, self.tower_info[0])-1
            for i in range(1, till):
                edit(EvalEdit(None, (known[i], None)))
            # for ev_move in known[1:till]:
            #     edit(EvalEdit(None, (ev_move, None)))
            edit(EvalEdit(None, (known[till], end)))
            if end and ev_len < self.tower_info[0]:
                edit(EvalEdit(None, None))

    def _decode_tower_edition(self, edit: TowerEdit) -> str:
        '''Decode a tower edition'''
        # assert isinstance(value, Plate) or value is None
        pad = self.config.border
        x_pos = edit.col*self.tower_info[1]+(pad << 1)+1
        y_pos = edit.row+pad+1

        value = self.plate_repr[edit.new or 0]

        return STR_AT_T % (y_pos, x_pos, value)

    def _decode_evaluation_edition(self, edit: EvalEdit) -> str:
        '''Decode an evaluation edition'''

        if new := edit.new:
            value = f'  {new[0]}{" "*6 if new[1] is None else " @    " if new[1] else " ...  "}'
        else:
            value = ' '*14

        padx = self.config.border*2
        pady = self.config.border
        pos_str = \
            Cursor.POS(self.tower_info.unit_width*3+padx*2+1,
                       edit.row+pady+1) if edit.row is not None else Cursor.DOWN(1)+Cursor.BACK(14)
        return f'{pos_str}{value}'

    def generate_repr(self) -> None:
        '''Generate the representation of the tower'''
        cfg = self.config
        info = TowerInfo.eval_tower_info(self.__tower, cfg.width)
        self.plate_repr = [draw_plate(
            plate, info.unit_width, info.half,
            show_plate_level=cfg.show_plate_level,
            plate_color=cfg.plate_color)
            for plate in range(1, self.tower_info[0]+1)]
        self.plate_repr.insert(0, draw_piller(
            info.unit_width, info.half, piller_color=cfg.piller_color))


STR_AT_T = '\033[%d;%dH%s'
DOUBLE_STR_AT_T = '\033[{};{}H{}\033[{};{}H{}'.format
# '''Return a string that moves the cursor to the given position and prints the value'''
