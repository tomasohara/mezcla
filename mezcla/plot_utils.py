#! /usr/bin/env python
#
## Miscellaneous mathplotlib utility functions
#

"""Plotting utility functions"""

def reset_plot():
    """Reset the mathplotlib state"""
    # Note: See https://stackoverflow.com/questions/741877/how-do-i-tell-matplotlib-that-i-am-done-with-a-plot
    # TODO: Make sure no other state retained

    # Clear the axes
    plt.cla()

    # Clear the figure
    plt.clf()
    return

if __name__ == '__main__':
    system.print_error("Warning: Not intended for direct invocation.")
