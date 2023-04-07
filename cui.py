'''cui henoi'''
from abc import ABC, abstractmethod
# from multiprocessing import Process, Queue, Pipe, connection
from time import perf_counter, sleep
import os
from sys import stdout
from typing import Literal
from colorama import Fore, Back, Cursor
from hanoilib import HenoiOrderFail, HenoiStepOver, Movement, Tower
from hanoilib.display import ShowConfiguration, Show
from true_false import true_false

# init(autoreset=True)

class Handler(ABC):
    '''To handle the environment'''
    config: ShowConfiguration

    def __init__(self, configuration: ShowConfiguration | None = None) -> None:
        self.config = configuration or ShowConfiguration()

    @staticmethod
    def error(log: str) -> Literal[False]:
        '''show error'''
        print(f'{Fore.RED}[Error] {log}{Fore.RESET}')
        return False

    @staticmethod
    def info(log: str) -> Literal[True]:
        '''show info'''
        print(f'{Fore.GREEN}[Info] {log}{Fore.RESET}')
        return True

    def eval(self, option: bool) -> bool:
        '''switch whether to show evaluation'''
        self.config.eval = option
        return True

    def width(self, option: str) -> bool:
        '''set the width of the tower'''
        if option in {'auto', 'half', 'full'}:
            self.config.width = option  # type: ignore
            return True
        return self.error(f'no option {option}')

    def level(self, option: bool) -> bool:
        '''switch whether to show plate level in the tower'''
        self.config.show_plate_level = option
        return True

    @abstractmethod
    def _show_tower(self) -> bool: ...

    @abstractmethod
    def help(self) -> bool:
        '''show help for user to use this program'''

    @abstractmethod
    def game(self, level: int) -> bool:
        '''create a new henoi-tower game with level plates'''

    @abstractmethod
    def move(self, movement: Movement) -> bool:
        '''move a plate from one position to another'''

    @abstractmethod
    def next(self) -> bool:
        '''move a step forward automatically'''

    @abstractmethod
    def flush(self) -> bool:
        '''flush the screen'''

    @abstractmethod
    def break_(self) -> bool:
        '''break the game'''

    @abstractmethod
    def play(self, time: float) -> bool:
        '''auto play the game'''

    def match_command(self, cmd: str) -> bool:
        '''match the command line and do the job'''
        match cmd.split():
            case 'help':
                return self.help()
            case 'game', level:
                return self.game(int(level))
            case 'move', from_, to:  # pylint: disable=invalid-name
                if from_ not in {'a', 'b', 'c'} or to not in {'a', 'b', 'c'}:
                    return self.error('only a, b and c are postions')
                move = Movement(ord(from_)-97, ord(to)-97)  # type: ignore
                return self.move(move)
            case 'next', :
                return self.next()
            case 'eval', option:
                if (arg := true_false(option)) is not None:
                    self.eval(arg)
                    self.flush()
                    return True
                return self.error(f'No such arguement {option}')
            case 'width', option:
                return self.width(option)
            case 'level', option:
                if (arg := true_false(option)) is not None:
                    self.level(arg)
                    self.flush()
                    return True
                return self.error(f'No such arguement {option}')
            case 'flush', :
                return self.flush()
            case 'break', :
                return self.break_()
            case 'play', :
                return self.play(10)
            case 'play', time:
                return self.play(int(time))
            case _:
                return self.error('no such cmd')


class DefaultHandler(Handler):
    '''Default handler'''
    show: Show | None

    def help(self) -> bool:
        return False

    def game(self, level: int) -> bool:
        self.show = Show(Tower.new(0, level), self.config)
        self._show_tower()

        return True

    def move(self, movement: Movement) -> bool:
        if self.show is None:
            return self.error('no tower to move')
        try:
            self.show.move(movement)
        except HenoiOrderFail:
            return self.error('invalid movement')
        print(self.show.read_editions(), end='')

        return True

    def next(self) -> bool:
        if self.show is None:
            return self.error('no tower to move')
        try:
            self.show.next()
        except HenoiStepOver:
            return self.error('already done')
        else:
            return True
        finally:
            print(self.show.read_editions(), end='')

    def flush(self) -> bool:
        try:
            self._show_tower()
        except AttributeError:
            return False
        return True

    def break_(self) -> bool:
        os.system('cls')
        self.show = None
        return True

    def play(self, time: float) -> bool:
        if self.show is None:
            return self.error('no tower to play')
        try:
            time = float(time)
            time_start = perf_counter()
            if time:
                while self.next():
                    sleep(5/time)
            else:
                self.show.fast_play(stdout.write)
            time_end = perf_counter()
            print("\033[F\033[K", end='')
            self.info('finish')
            self.info(f'time: {time_end-time_start:.3f}s')
            return True
        except ValueError:
            return self.error('time should be int or float')
        except KeyboardInterrupt:
            self.info('stop going')
            return False

    def _show_tower(self) -> bool:
        if self.show is None:
            self.error('no tower to do so')
            return False
        os.system('cls')
        print(str(self.show))
        return True


SEP = '-'*32


def main():
    '''main function'''
    # pylint: disable=broad-exception-caught
    handler = DefaultHandler()
    while True:
        try:
            handler.match_command(input('>>> '))
        except (KeyboardInterrupt, EOFError):
            leave = input(f'{Fore.CYAN}\n\033[F\033[K{SEP}\n'
                          '\033[K>>> \n'
                          f'Do you want to leave? [yes / no]\033[F{Cursor.FORWARD(4)}{Fore.RESET}')
            while True:
                if (t_f := true_false(leave)) is True:
                    os.system('cls')
                    print(f'{Fore.BLUE}Thank for using the program, good bye!')
                    return
                if t_f is False:
                    print(f'{Fore.CYAN}Do you want to leave?\n{SEP}{Fore.RESET}')
                    break
                leave = input(f'{Fore.CYAN}\033[2F\033[K{SEP}\n'
                            '\033[K>>> \n'
                            f'Do you want to leave? [yes / no]'
                            f'\033[F{Cursor.FORWARD(4)}{Fore.RESET}')
        except Exception as exc:
            Handler.error(f'{exc.args} {exc.__class__.__name__}')


if __name__ == '__main__':
    # while True:
    os.system('cls')
    try:
        main()
    except KeyboardInterrupt:
        # print('\n','\033[K\033[F'*3, sep='')
        # continue
        os.system('cls')
        print(f'{Fore.BLUE}\nThank for using the program, good bye!')

# end
