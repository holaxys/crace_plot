import sys

import crace.errors as CE
from crace_plot.plot_options import PlotOptions
from crace_plot.load_data import ReadExperiments, ReadConfigurations
from crace_plot.draw import DrawMethods as draw

class CracePlot:
    """
    Class defines the procedure to select one drawMethod for drawing plot
    :ivar drawMethod: the method used to draw plot for provided Crace results
    """
    def __init__(self, options: PlotOptions ) -> None:

        self.out_dir = options.outDir.value
        self.drawMethod = options.drawMethod.value
        self.dataType = options.dataType.value

        try:
            if self.dataType in ["e", "exp", "exps" ,"experiments"]:
                data = ReadExperiments(options)
            elif self.dataType in ["c", "config", "configs", "configurations"]:
                data = ReadConfigurations(options)

        except CE.PlotError as err:
            print("\nERROR: There was an error while drawing plot: ")
            print(err)
            sys.tracebacklimit = 0
            raise

