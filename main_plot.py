import sys

import plot.containers.read_options as rd
from plot.draw.plot import DrawPlot

def start_cmdline(arguments=None):
    """
    Function that executes the crace plot with arguments from the command line

    :param arguments: 
    """

    args = arguments[1:]

    _check_args(args=args)

    try:
        Reader = rd.ParseOptions.from_input(arguments)

        if Reader.execDir.value is not None and Reader.drawMethod.value is not None:
            DrawPlot(Reader)

    except Exception as e:
        print("! There was an error while executing crace plot:")
        print(e)
        raise e

def _check_args(args):

    # check for number of imputs
    if len(args) < 1:
        print("! At least an option must be provided to load crace-plot options")
        rd.print_info()
        sys.exit()  

    # check for help command
    if "-h" in args or "--help" in args:
        rd.print_help()
        sys.exit()

    # check for version command
    if "-v" in args or "--version" in args:
        rd.print_version()
        sys.exit()  

if __name__ == '__main__':
    arguments = sys.argv
    start_cmdline(arguments)

    