from pydantic import validate_call
"""
Some docs here
"""
from mezcla import debug


def not_called_function() ->None:
    """This function is not called"""
    print('This function is not called')
    print(debug.get_level())


def move_debug_level() ->None:
    """Move debug level"""
    debug.set_level(debug.get_level() + 1)
    debug.set_level(debug.get_level() - 1)


def main() ->None:
    """Main function"""
    validate_call(move_debug_level)()
    print('Hello, World!')


if __name__ == '__main__':
    validate_call(main)()
