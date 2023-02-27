

import os
import re
import copy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(rc={'figure.figsize':(11.7,8.27)})

# import plotly as py
import plotly.graph_objects as go
# py.offline.init_notebook_mode(connected=True)

import plotly.express as px

# from pyecharts import options as opts
# from pyecharts.charts import Page, Parallel

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
        self.key_param = options.keyParameter.value

        if options.numConfigurations.value == "elites":
            self.num_config = 5
        elif options.numConfigurations.value == "elitist":
            self.num_config = 1
        elif options.numConfigurations.value == "all":
            self.num_config = -1
        elif options.numConfigurations.value == "else":
            self.num_config = options.elseNumConfigs.value

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

    def parallelplot(self):
        """
        call the function to draw boxplot
        """
        self.draw_parallelplot(self.all_results, self.exp_names, self.elite_ids, self.parameters)

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
        data_new.drop(columns=['exp_name', 'config_id'], inplace=True)

        map_dic = {}
        new_parameters = copy.deepcopy(parameters)
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
        new_parameters.pop('dlb_id', None)
        new_parameters.pop('nnls', None)
        new_parameters.pop('elitistants', None)
        new_parameters.pop('rasrank', None)
        data_new.drop(columns=['nnls', 'dlb_id', 'elitistants', 'rasrank'], inplace=True)
        print(data_new)
        # print(parameters)
        # print(new_parameters)

        if self.num_config != -1:
            ids = re.sub('}','',re.sub('{','',re.sub('\'','',str(elite_ids))))
            print("#   {}".format(ids))

            plot_dict = []
            each_dict = {}
            for name in new_parameters.keys():
                each_dict = dict(
                    range = new_parameters[name]['domain'],
                    label = name, 
                    values = data_new[name]
                )
                plot_dict.append(each_dict)
             
            print('---------------------------------------------------------------\n')

            fig = go.Figure(data=
            go.Parcoords(
                line = dict(color = data_new['algorithm_id'],
                            colorscale = 'Tealrose',
                            showscale = True,
                            cmin = -200,
                            cmax = 200),
            #     dimensions = list([
            #         dict(range = [0.0, 5.0],
            #             label = 'alpha', values = data_new['alpha']),
            #         dict(range = [0.0, 10.0],
            #              label = 'beta', values = data_new['beta']),
            #         dict(range = [0.01, 1.0], 
            #              label = 'rho', values = data_new['rho']),
            #         dict(range = [5, 100],
            #              label = 'ants', values = data_new['ants']),
            #         dict(range = [0.0, 1.0],
            #              label = 'q0', values = data_new['q0']),
            #         # dict(range = [1, 100], 
            #         #     label = 'rasrank', values = data_new['rasrank']),
            #         dict(range = [0,4],
            #             label = 'algorithm', values = data_new['algorithm_id']),
            #         dict(range = [0, 3],
            #              label = 'localsearch', values = data_new['localsearch_id'])
            #     ])
            # ))
                dimensions = list([line for line in plot_dict])
            ))
            fig.show()

    def draw_parallelplot(self, data, exp_names, elite_ids, parameters):
        """
        Use data to draw a boxplot for the top5 elite configurations
        """

        num = len(data)

        print("#\n# The Crace results:")
        print(data)
        print("#\n# The experiment name(s) of the Crace results you provided:")
        print("# ", re.sub('\'','',str(exp_names)))
        print("#")

        data_new = data.copy()

        parameters['exp_name'] = {}
        parameters['exp_name']['type'] = 'c'
        parameters['exp_name']['domain'] = exp_names

        if self.num_repetitions == 1:
            parameters['config_id'] = {}
            parameters['config_id']['type'] = 'i'
            parameters['config_id']['domain'] = [1, int(data['config_id'].max())]
            self.key_param = 'config_id'

        new_parameters = []
        new_parameters = copy.deepcopy(parameters)

        map_dic = {}
        for name in parameters.keys():
            if parameters[name]['type'] == 'c':
                i = 0
                map_dic[name] = {}
                new_parameters[name]['domain'] = []
                for a in parameters[name]['domain']:
                    map_dic[name][a] = i
                    new_parameters[name]['domain'].append(i)
                    i += 1
                data_new[name] = data[name].map(map_dic[name])

        col1 = data_new.count() == 0
        for i in range(len(col1)):
            name = col1.index[i]
            per = list(data[name]).count('null')/float(num)
            if per > 0:
                if new_parameters[name]['type'] != 'c':
                    old = copy.deepcopy(new_parameters[name]['domain'])
                    new_parameters[name]['domain'][0] = old[0]-1
                    print("! WARNING: 'null' values in {} has been replaced by {}.".format(name, old[0]-1))
                    data_new[name].replace('null', old[0]-1, inplace=True)
                else:
                    old = copy.deepcopy(parameters[name]['domain'])
                    new_parameters[name]['domain'].append(len(old))
                    parameters[name]['domain'].append('null')
                    print("! WARNING: {} has 'null' values.".format(name))
            if col1[i]:
                print("! WARNING: all values in {} are NaN, it will be deleted for the plot!".format(name) )
                new_parameters.pop(col1.index[i])

        print("#\n# The new parameters:")
        print(new_parameters.keys())
        print("#\n# The new Crace results:")
        print(data_new)

        if self.num_config != -1:
            print("#\n# Elite configurations from the Crace results you provided that will be analysed here :")
            # ids = re.sub('}','',re.sub('{','',re.sub('\'','',str(elite_ids))))
            for a in elite_ids.keys():
                print("#   {}: {}".format(a, elite_ids[a]))

            plot_dict = []
            each_dict = {}
            for name in new_parameters.keys():
                if new_parameters[name]['type'] != 'c':
                    each_dict = dict(
                        range = new_parameters[name]['domain'],
                        label = name, 
                        values = data_new[name]
                    )
                else:
                    each_dict = dict(
                        tickvals = new_parameters[name]['domain'],
                        ticktext = parameters[name]['domain'],
                        label = name, 
                        values = data_new[name]
                    )
                plot_dict.append(each_dict)
            
            keyParam = ""
            cmax = 0
            if self.key_param not in ('null', None):
                keyParam = self.key_param
            else:
                keyParam = 'exp_name' 
            if parameters[keyParam]['type'] != 'c':
                cmax = parameters[keyParam]['domain'][1]
            else:
                cmax = len(parameters[keyParam]['domain'])
            fig = go.Figure(data=
            go.Parcoords(
                line = dict(color = data_new[keyParam],
                            colorscale = 'Tealrose',
                            showscale = True,
                            cmin = 0,
                            cmax = cmax),
                dimensions = list([line for line in plot_dict])
            ))
            fig.show()

        else:
            print("#\n# Elite configurations from the Crace results you provided that will be analysed here :")
            # ids = re.sub('}','',re.sub('{','',re.sub('\'','',str(elite_ids))))
            for a in elite_ids.keys():
                print("#   {}: {}".format(a, elite_ids[a]))

            plot_dict = []
            each_dict = {}
            for name in new_parameters.keys():
                if new_parameters[name]['type'] != 'c':
                    each_dict = dict(
                        range = new_parameters[name]['domain'],
                        label = name, 
                        values = data_new[name]
                    )
                else:
                    each_dict = dict(
                        tickvals = new_parameters[name]['domain'],
                        ticktext = parameters[name]['domain'],
                        label = name, 
                        values = data_new[name]
                    )
                plot_dict.append(each_dict)

            keyParam = ""
            cmax = 0
            if self.key_param not in ('null', None):
                keyParam = self.key_param
            else:
                keyParam = 'exp_name' 
            if parameters[keyParam]['type'] != 'c':
                cmax = parameters[keyParam]['domain'][1]
            else:
                cmax = len(parameters[keyParam]['domain'])
            fig = go.Figure(data=
            go.Parcoords(
                line = dict(color = data_new[keyParam],
                            colorscale = 'Tealrose',
                            showscale = True,
                            cmin = 0,
                            cmax = cmax),
                dimensions = list([line for line in plot_dict])
            ))
            fig.show()
