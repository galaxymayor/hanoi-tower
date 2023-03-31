'''This is a simple program that asks the user a question and then\
 identifies the answer as true or false.'''


TRUE_SET = {
    'true',
    't',
    'y',
    'yes',
    '1',
    'v',
    'sure',
    'ok',
    'definitely',
    'absolutely',
    'yep',
    'confirm'
}

FALSE_SET = {
    'false',
    'f',
    'n',
    'no',
    '0',
    'x',
    'not',
    'nope',
    'cancel',
}


def true_false(string: str) -> bool | None:
    '''return True if the string is determined to be true, False if it is\
       determined to be false, and None if it is not determined'''
    string = string.lower()
    if string in TRUE_SET:
        return True
    if string in FALSE_SET:
        return False
    for true in TRUE_SET:
        if true in string:
            return True
    for false in FALSE_SET:
        if false in string:
            return False
    return None
