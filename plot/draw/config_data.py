

import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(rc={'figure.figsize':(11.7,8.27)})

import plotly as py
import plotly.graph_objs as go
# py.offline.init_notebook_mode(connected=True)

from plot.containers.read_options import ReadOptions
from plot.draw.data import ReadResults


class Parameters:
    """
    Class defines a list of methods used to compare configurations from Crace
    :ivar exec_dir: the directory of Crace results
    :ivar num_repetitions: the number of repetitions of the provided Crace results
    :ivar title: the title of output plot
    :ivar file_name: the full address and name of the output plot file
    :ivar elitist: analyse the elitist configuration or not
    :ivar all: analyse all configurations or not
    """
    def __init__(self, options: ReadOptions ):

        self.exec_dir = options.execDir.value
        self.out_dir = options.outDir.value
        self.num_repetitions = options.numRepetitions.value
        
        self.title = options.title.value
        self.file_name = options.fileName.value

        if options.numConfigurations.value == "elites":
            self.num_config = 5
        elif options.numConfigurations.value == "elitist":
            self.num_config = 1
        else:
            self.num_config = -1

        # select exact method to draw plot via :param{drawMethod}
        # e.g.: boxplot, violinplot
        self.draw_method = options.drawMethod.value

        exp_folders = sorted([subdir for subdir, dirs, files in os.walk(self.exec_dir) \
                      for dir in dirs if dir == 'irace_log' ])
        print("# Loading Crace results..")
        self.load = ReadResults(exp_folders, options)

        self.all_results, self.exp_names, self.elite_ids, self.parameters = self.load.load_for_configs_data()
    
    def lineplot(self):
        """
        call the function to draw boxplot
        """
        self.draw_lineplot(self.all_results, self.exp_names, self.elite_ids, self.parameters)

    def draw_lineplot(self, data, exp_names, elite_ids, parameters):
        """
        Use data to draw a boxplot for the top5 elite configurations
        """

        num = self.num_repetitions

        print("#\n# The Crace results:")
        print(data)
        print("#\n# The experiment name(s) of the Crace results you provided:")
        print("# ", re.sub('\'','',str(exp_names)))
        print("#\n# Elite configurations from the Crace results you provided that will be analysed here :")

        data_new = data.copy()
        data_new.drop(columns=['exp_name'], inplace=True)

        map_dic = {}
        new_parameters = parameters.copy()
        for name in parameters.keys():
            if parameters[name]['type'] == 'c':
                i = 0
                map_dic[name] = {}
                new_parameters[name+'_id'] = {}
                new_parameters[name+'_id']['domain'] = [0]
                new_parameters.pop(name, None)
                for a in parameters[name]['domain']:
                    map_dic[name][a] = i
                    # new_parameters[name+'_id']['domain'].append(i)
                    i += 1
                new_parameters[name+'_id']['domain'].append(i-1)
                data_new[name+'_id'] = data_new[name].map(map_dic[name])
                data_new.drop(columns=name, inplace=True)
        print(parameters)
        print(new_parameters)

        if self.num_config == 1:
            ids = re.sub('}','',re.sub('{','',re.sub('\'','',str(elite_ids))))
            print("#   {}".format(ids))

            plot_dict = []
            for name in new_parameters.keys():
                tmp = dict(range = new_parameters[name]['domain'],
                        label = name, 
                        values = data_new[name])
                plot_dict.append(tmp)

            fig = py.offline.plot({
                "data": [go.Parcoords(
                        line = dict(color = 'green' ),
                        dimensions = plot_dict
                    )],
                "layout": go.Layout(title='TEST')
            })

            # schema = parameters.keys()
            # data_new = np.array(data_new[schema]).tolist()

            # fig = Parallel('TEST')
            # fig.config(schema)
            # fig.add('TEST', data_new, is_random = True)
