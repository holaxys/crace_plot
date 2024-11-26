import re
import sys
import inspect
import traceback

from crace_plot.plot_options import PlotOptions as po
from crace_plot.plot import CracePlot
import crace.errors as CE

def _check_args(args):

    # check for number of imputs
    if len(args) < 1:
        print("ERROR: At least an option must be provided to execute crace-plot")
        po.print_info()
        sys.tracebacklimit = 0
        raise CE.OptionError("ERROR: At least an option must be provided to execute crace-plot")

def start_cmdline(arguments=None, console: bool=True):
    """
    Function that executes the crace plot with arguments from the command line

    :param arguments: 
    """

    try:
        _check_args(args=arguments)
        options = po(arguments)
        CracePlot(options)
    except Exception as e:
        if any(isinstance(e, cls) for cls in [x[1] for x in inspect.getmembers(CE, inspect.isclass)]):
           pass
            # err_info = traceback.format_exc()
            # print(err_info)
        else:
            print("\nERROR: There was an error while executing crace plot:")
            err_info = traceback.format_exc()
            print(err_info)
    finally:
        if not console: sys.exit()

def crace_plot(arguments: list=None, console: bool=True):
    """
    Allowed to be called: 1. by entry point at terminal,
                          2. at python console
    """
    if not isinstance(arguments, list):
        if isinstance(arguments, str):
            arguments = re.split(r"[ ,]+", arguments)
    if not arguments:
        # arguments may be [] (must not be None)
        arguments = sys.argv[1:] # command line arguments as a list

    start_cmdline(arguments, console)

if __name__ == '__main__':
    crace_plot(console=False)
