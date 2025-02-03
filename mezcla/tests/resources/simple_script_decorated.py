from pydantic import validate_call
"""
Some docs here
"""
from mezcla import debug


def not_called_function() ->None:
    """This function is not called"""
    print('This function is not called')
    print(validate_call(debug.get_level)())


def move_debug_level() ->None:
    """Move debug level"""
    print('Default debug level: ', debug.DEFAULT)
    print('Current debug level: ', validate_call(debug.get_level)())
    validate_call(debug.set_level)(validate_call(debug.get_level)() + 1)
    validate_call(debug.set_level)(validate_call(debug.get_level)() - 1)


def main() ->None:
    """Main function"""
    print('Hello, ...')
    validate_call(move_debug_level)()
    print('... World!')


if __name__ == '__main__':
    validate_call(main)()
