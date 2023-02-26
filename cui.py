'''cui henoi'''
import os
import sys
from time import sleep
from typing import Literal
from hanoilib import HenoiOrderFail, HenoiStepOver, Movement, Tower
from hanoilib.show import show

TRUE_SET = {
    'true',
    't',
    'y',
    'yes',
    '1',
    'v'
}

FALSE_SET = [
    'false',
    'f',
    'n',
    'no',
    '0',
    'x'
]


class Handler:
    '''To handle the environment'''
    tower: Tower | None = None
    eval: bool = False
    width: Literal['auto', 'half', 'full'] = 'auto'
    show_level: bool = False

    def match_command(self, cmd: str) -> bool:
        match cmd.split():
            case 'help':
                return False
            case 'game', level:
                level = int(level)
                self.tower = Tower.new(0, level)
                self.show_tower()
                return True
            case 'move', from_, to:
                if self.tower is None:
                    return self.error('no tower to move')
                if from_ not in {'a', 'b', 'c'} or to not in {'a', 'b', 'c'}:
                    return self.error('only a, b and c are postions')
                move = Movement(from_, to) # type: ignore
                try:
                    self.tower.move(move)
                except HenoiOrderFail:
                    return self.error('invalid movement')
                else:
                    self.show_tower()
                    return True
            case 'next', :
                if self.tower is None:
                    return self.error('no tower to do so')
                try:
                    next_step = next(self.tower.eval())
                except HenoiStepOver:
                    return self.error('already done')
                else:
                    self.tower.move(next_step)
                    self.show_tower()
                    return True
            case 'eval', option:
                if option in TRUE_SET:
                    self.eval = True
                    return True
                if option in FALSE_SET:
                    self.eval = False
                    return True
                return self.error(f'no option {option}')
            case 'width', option:
                if option in {'auto', 'half', 'full'}:
                    self.width = option # type: ignore
                    return True
                return self.error(f'no option {option}')
            case 'level', option:
                if option in TRUE_SET:
                    self.show_level = True
                    return True
                if option in FALSE_SET:
                    self.show_level = False
                    return True
                return self.error(f'no option {option}')
            case 'flush', :
                self.show_tower()
                return True
            case 'break', :
                os.system('cls')
                self.tower = None
                return True
            case 'play',:
                return self.match_command('play 10')
            case 'play', time :
                try:
                    time = float(time)
                    while self.match_command('next'):
                        if time:
                            sleep(5/time)
                    sys.stdout.write("\033[F")
                    sys.stdout.write("\033[K")
                    print('[Info] finish')
                    return True
                except ValueError:
                    return self.error('time should be int or float')
                except KeyboardInterrupt:
                    print('[Info] stop going')
                    return False
            case _ :
                return self.error('no such cmd')
                
    def show_tower(self) -> bool:
        if self.tower is None:
            self.error('no tower to do so')
            return False
        os.system('cls')
        print(show(self.tower, self.width,
                   show_plate_level=self.show_level, evaluation=self.eval,
                   bd=True))
        return True
    
    @staticmethod
    def error(log: str) -> Literal[False]:
        '''show error'''
        print(f'[Error] {log}')
        return False



def main():
    # pylint: disable=broad-exception-caught
    handler = Handler()
    while True:
        try:
            handler.match_command(input('>>> '))
        except Exception as exc:
            print(f'[Error] {exc.args}')
        except KeyboardInterrupt:
            leave = input('\n\033[F\033[K--------------------------------\n'
                            '\033[K>>> \n'
                            'Do you want to leave? [yes / no]\033[F\033[4C')
            while True:
                if leave in FALSE_SET:
                    print('Do you want to leave?\n--------------------------------')
                    break
                if leave in TRUE_SET:
                    print('Thank for using the program, good bye!')
                    sys.exit()
                leave = input('\033[2F\033[K--------------------------------\n'
                              '\033[K>>> \n'
                              'Do you want to leave? [yes / no]\033[F\033[4C')



if __name__ == '__main__':
    main()

#end
