import copy
import json
import os
import sys

import crace
from crace_plot.plot_options import PlotOptions
from crace_plot.draw import DrawExps, DrawConfigs
import pandas as pd


class ReadCraceResults:
    def __init__(self, options: PlotOptions):
        self.exec_dir = options.execDir.value
        self.exp_folders = sorted([subdir for subdir, dirs, files in os.walk(self.exec_dir) \
                      for dir in dirs if dir == 'race_log' ])
        self.exp_names = []
        self.results = {}
        self.elites = {}

        for folder in self.exp_folders:
            name = os.path.basename(folder)
            self.exp_names.append(name)

            self.results[name] = crace.crace_cmdline(f'--read, {folder}, --readlogs_in_plot, 1')
            print('#------------------------------------------------------------------------------')

            self.elites[name] = self.results[name].elites

        self.parameters = self.parse_parameters(self.results[name].parameters)

    def parse_parameters(self, parameters):
        """
        load the range of each parameter in the provided Crace results
        """
        # parse all parameters
        all_parameters = {}
        tmp_params = parameters.get_names()
        for p in tmp_params:
            all_parameters[p] = {}
            all_parameters[p]['type'] = parameters.get_parameter(p).type
            all_parameters[p]['domain'] = parameters.get_parameter(p).domain

        return(all_parameters)

class ReadExperiments(ReadCraceResults):
    def __init__(self, options: PlotOptions):
        super().__init__(options)

        self.experiments = pd.DataFrame()
        if options.test.value:
            for name in self.exp_names:
                df = copy.deepcopy(self.results[name].test.data.dropna())
                df.insert(0, 'exp_name', name)
                self.experiments = pd.concat([self.experiments, df], ignore_index=True)

        else:
            for name in self.exp_names:
                df = copy.deepcopy(self.results[name].training.data.dropna())
                df.insert(0, 'exp_name', name)
                self.experiments = pd.concat([self.experiments, df], ignore_index=True)

        self.de = DrawExps(options=options, data=self.experiments, exp_names=self.exp_names, elite_ids=self.elites, parameters=self.parameters)

    def boxplot(self):
        """
        call the function to draw boxplot
        """
        self.de.draw_boxplot(self.experiments, self.exp_names, self.elites)

    def violinplot(self):
        """
        call the function to draw violinplot
        """
        self.de.draw_violinplot(self.experiments, self.exp_names, self.elites) 

class ReadConfigurations(ReadCraceResults):
    def __init__(self, options: PlotOptions):
        super().__init__(options)

        data = self.results.configurations

        # config_list = [x.get_values() for x in data.all_configurations.values()]
        # df = pd.DataFrame(config_list)

        self.dc = DrawConfigs(options=options, data=data, exp_names=self.exp_names, elite_ids=self.elites, parameters=self.parameters)

    def parallelcoord(self):
        """
        call the function to draw parallel coord plot
        """
        self.dc.draw_parallelcoord(self.experiments, self.exp_names, self.elites, self.parameters)

    def parallelcat(self):
        """
        call the function to draw parallel categorical plot
        """
        self.dc.draw_parallelcat(self.experiments, self.exp_names, self.elites, self.parameters)

    def piechart(self):
        """
        call the function to draw pie chart
        """
        self.dc.draw_piechart(self.experiments, self.parameters)

    def pairplot(self):
        """
        call the function to draw scatter matrix plot
        """
        self.dc.draw_pairplot(self.experiments, self.exp_names, self.parameters)

    def histplot(self):
        """
        call the function to draw distplot
        """
        self.dc.draw_histplot(self.experiments, self.parameters)

    def boxplot(self):
        """
        call the function to draw distplot
        """

        self.dc.draw_boxplot(self.experiments, self.parameters)

    def heatmap(self):
        """
        call the function to draw distplot
        """
        self.dc.draw_heatmap(self.experiments, self.parameters)

    def jointplot(self):
        """
        call the function to draw jointplot
        """
        self.dc.draw_jointplot(self.experiments, self.exp_names, self.parameters)
