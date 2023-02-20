import os
import sys

from plot.containers.read_options import ReadOptions
from plot.draw.performance import Performance

class DrawPlot:
    """
    Class defines the procedure to select one drawMethod for drawing plot
    :ivar drawMethod: the method used to draw plot for provided Crace results
    """
    def __init__(self, reader: ReadOptions ) -> None:

        # self.options = reader.options
        # self.arguments = reader.arguments
        # self.exec_dir = reader.execDir.value
        # self.out_dir = reader.outDir.value
        self.drawMethod = reader.drawMethod.value
        # self.num_repetitions = reader.numRepetitions.value
        # self.title = reader.title.value
        # self.file_name = reader.fileName.value

        if self.drawMethod in ("boxplot_test", "boxplot_training"):
            load = Performance(reader)
            getattr(load, self.drawMethod)()

    def run(self):
        
        print("run")
