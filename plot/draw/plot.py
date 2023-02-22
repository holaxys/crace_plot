import os
import sys
import traceback

from plot.containers.read_options import ReadOptions
from plot.draw.performance import Performance
from plot.draw.config_data import Parameters

class DrawPlot:
    """
    Class defines the procedure to select one drawMethod for drawing plot
    :ivar drawMethod: the method used to draw plot for provided Crace results
    """
    def __init__(self, reader: ReadOptions ) -> None:

        self.out_dir = reader.outDir.value
        self.drawMethod = reader.drawMethod.value

        try:
            if self.drawMethod in ('boxplot', 'violinplot'):
                load = Performance(reader)
            elif self.drawMethod in ('lineplot'):
                load = Parameters(reader)
            getattr(load, self.drawMethod)()

            print('#\n# Succeeded! ')
            print('# Now you can check the plot file in', self.out_dir)
            print('#------------------------------------------------------------------------------')
        except:
            print("#\n! There was an error: ")
            err = traceback.format_exc()
            print(err)
            sys.exit()

