

import os
import re
import copy
import numpy as np
import pandas as pd
import seaborn as sns
sns.set(rc={'figure.figsize':(11.7,8.27)})

# import plotly as py
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt

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
        self.matrix_param = options.matrixParameters.value
        self.catx = options.catx.value
        self.caty = options.caty.value

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

        print("#\n# The Crace results:")
        print(self.all_results,)
        print("#\n# The experiment name(s) of the Crace results you provided:")
        print("# ", re.sub('\'','',str(self.exp_names)))
        print("#")

    def parallelcoord(self):
        """
        call the function to draw parallel coord plot
        """
        self.draw_parallelcoord(self.all_results, self.exp_names, self.elite_ids, self.parameters)

    def parallelcat(self):
        """
        call the function to draw parallel categorical plot
        """
        self.draw_parallelcat(self.all_results, self.exp_names, self.elite_ids, self.parameters)

    def piechart(self):
        """
        call the function to draw pie chart
        """
        self.draw_piechart(self.all_results, self.exp_names, self.parameters)

    def scattermatrix(self):
        """
        call the function to draw scatter matrix plot
        """
        self.draw_scattermatrix(self.all_results, self.exp_names, self.parameters)

    def draw_parallelcoord(self, data, exp_names, elite_ids, parameters):
        """
        Use data to draw a parallel coord plot for the provided Crace results
        """

        num = len(data)

        data_new = data.copy()
        keyParam = ""

        if self.num_repetitions == 1:
            parameters['config_id'] = {}
            parameters['config_id']['type'] = 'i'
            parameters['config_id']['domain'] = [int(data['config_id'].min()), int(data['config_id'].max())]
            keyParam = 'config_id'
        else:
            parameters['exp_name'] = {}
            parameters['exp_name']['type'] = 'c'
            parameters['exp_name']['domain'] = exp_names
            keyParam = 'exp_name'

        if self.key_param not in ('null', None):
            keyParam = self.key_param
        else:
            keyParam = keyParam 

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

        print("#\n# Elite configurations from the Crace results you provided that will be analysed here :")
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
        
        cmin = 0
        cmax = 0
        
        if parameters[keyParam]['type'] != 'c':
            cmin = parameters[keyParam]['domain'][0]
            cmax = parameters[keyParam]['domain'][1]
            data_key = pd.to_numeric(data_new[keyParam])
        else:
            cmin = 0
            cmax = len(parameters[keyParam]['domain'])
            data_key = data_new[keyParam]

        fig = go.Figure(data=
        go.Parcoords(
            line = dict(color = data_key,
                        colorscale = 'Tealrose',
                        showscale = True,
                        cmin = cmin,
                        cmax = cmax),
            dimensions = list([line for line in plot_dict])
        ))
        fig.show()

    def draw_parallelcat(self, cat_data, exp_names, elite_ids, parameters):
        """
        Use data to draw a parallel categorical plot for the provided Crace results
        """

        num = len(cat_data)

        if self.num_repetitions == 1:
            parameters['config_id'] = {}
            parameters['config_id']['type'] = 'i'
            parameters['config_id']['domain'] = [int(cat_data['config_id'].min()), int(cat_data['config_id'].max())]
            keyParam = 'config_id'
        else:
            parameters['exp_name'] = {}
            parameters['exp_name']['type'] = 'c'
            parameters['exp_name']['domain'] = exp_names
            keyParam = 'exp_name'

        new_parameters = []
        new_parameters = copy.deepcopy(parameters)

        col1 = cat_data.count() == 0
        for i in range(len(col1)):
            name = col1.index[i]
            per = list(cat_data[name]).count('null')/float(num)
            if col1[i]:
                print("! WARNING: all values in {} are NaN, it will be deleted for the plot!".format(name) )
                new_parameters.pop(col1.index[i])
            if per > 0:
                if new_parameters[name]['type'] != 'c':
                    old = copy.deepcopy(new_parameters[name]['domain'])
                    new_parameters[name]['domain'][0] = old[0]-1
                    print("! WARNING: 'null' values in {} has been replaced by {}.".format(name, old[0]-1))
                    cat_data[name].replace('null', old[0]-1, inplace=True)
                else:
                    old = copy.deepcopy(parameters[name]['domain'])
                    new_parameters[name]['domain'].append(len(old))
                    parameters[name]['domain'].append('null')
                    print("! WARNING: {} has 'null' values.".format(name))


        print("#\n# The new parameters:")
        print(new_parameters.keys())

        print("#\n# Elite configurations from the Crace results you provided that will be analysed here :")
        for a in elite_ids.keys():
            print("#   {}: {}".format(a, elite_ids[a]))

        plot_dict = []
        each_dict = {}
        for name in new_parameters.keys():
            if new_parameters[name]['type'] == 'c':
                each_dict = dict(
                    label = name, 
                    values = cat_data[name]
                )
                plot_dict.append(each_dict)
        
        color = np.zeros(len(plot_dict), dtype='uint8')
        colorscale = [[0, 'gray'], [1, 'firebrick']]
        
        # Build figure as FigureWidget
        fig = go.FigureWidget(data=[
        go.Scatter(
            x = cat_data[self.catx],
            y = cat_data[self.caty],
            marker={'color': 'gray'},
            mode='markers',
            selected={'marker': {'color': 'firebrick'}},
            unselected={'marker': {'opacity': 0.3}}
        ), 
        go.Parcats(
                domain={'y': [0, 0.4]}, 
                dimensions=list([line for line in plot_dict]),
                line={'colorscale': colorscale, 'cmin': 0, 'cmax': 1, 'color': color, 'shape': 'hspline'}),
        ])

        fig.update_layout(
            height=1000, 
            xaxis={'title': self.catx},
            yaxis={'title': self.caty, 'domain': [0.6, 1]},
            dragmode='lasso', 
            hovermode='closest',
            overwrite=True)

        # Update color callback
        def update_color(trace, points, state):
            # Update scatter selection
            fig.data[0].selectedpoints = points.point_inds

            # Update parcats colors
            new_color = color
            new_color[points.point_inds] = 1
            fig.data[1].line.color = new_color

        # Register callback on scatter selection...
        fig.data[0].on_selection(update_color)
        # and parcats click
        fig.data[1].on_click(update_color)

        fig.show()

    def draw_piechart(self, pie_data, exp_names, parameters):
        """
        Use pie_data to draw a pie plot for the provided Crace results
        """

        num = len(pie_data)

        data = copy.deepcopy(pie_data)
        new_parameters = copy.deepcopy(parameters)

        col1 = data.count() == 0
        for i in range(len(col1)):
            name = col1.index[i]
            per = list(data[name]).count('null')/float(num)
            if col1[i]:
                print("! WARNING: all values in {} are NaN, it will be deleted for the plot!".format(name) )
                new_parameters.pop(col1.index[i])
            if per > 0:
                if new_parameters[name]['type'] != 'c':
                    old = copy.deepcopy(new_parameters[name]['domain'])
                    new_parameters[name]['domain'][0] = old[0]-1
                    print("! WARNING: 'null' values in {} has been replaced by {}.".format(name, old[0]-1))
                    data[name].replace('null', old[0]-1, inplace=True)
                else:
                    old = copy.deepcopy(parameters[name]['domain'])
                    new_parameters[name]['domain'].append(len(old))
                    parameters[name]['domain'].append('null')
                    print("! WARNING: {} has 'null' values.".format(name))


        subgroup = {}
        for name in new_parameters.keys():
            subgroup[name] = {}
            subgroup[name]['names'] = []
            subgroup[name]['props'] = []
            if new_parameters[name]['type'] != 'c':
                data[name] = pd.to_numeric(data[name])
                left = parameters[name]['domain'][0]
                right = parameters[name]['domain'][1]
                tmp = (left+right)/3
                sub1 = '[{:.2f}, {:.2f}]'.format(left, tmp)
                sub2 = '[{:.2f}, {:.2f}]'.format(tmp, 2*tmp)
                sub3 = '[{:.2f}, {:.2f}]'.format(2*tmp, right)

                subgroup[name]['names'].append(sub1)
                s_bool = ((data[name] >= left) & (data[name] < tmp))
                subgroup[name]['props'].append(s_bool.sum())

                subgroup[name]['names'].append(sub2)
                s_bool = ((data[name] >= tmp) & (data[name] < 2*tmp))
                subgroup[name]['props'].append(s_bool.sum())

                subgroup[name]['names'].append(sub3)
                s_bool = ((data[name] >= 2*tmp) & (data[name] <= right))
                subgroup[name]['props'].append(s_bool.sum())

                if sum(subgroup[name]['props']) < len(data[name]):
                    subgroup[name]['names'].append('null')
                    s_bool = (data[name] < left)
                    subgroup[name]['props'].append(s_bool.sum())
                
            else:
                for x in parameters[name]['domain']:
                    subgroup[name]['names'].append(x)
                    s_bool = data[name] == x
                    subgroup[name]['props'].append(s_bool.sum())

        num = len(new_parameters.keys())
        labels = [self.title]
        values = [0]
        parents = [""]
        for name in new_parameters.keys():
            i = 0
            labels.append(name)
            values.append(self.count_values(pie_data[name]))
            parents.append(self.title)
            for label in subgroup[name]['names']:
                labels.append(label)
                values.append(subgroup[name]['props'][i])
                parents.append(name)
                i += 1
        # print(values, '\n')
        # print(labels, '\n')
        # print(parents)

        fig = go.Figure(go.Sunburst(
            labels = labels,
            parents = parents,
            values = values
        ))
        fig.update_layout(margin = dict(t=0, l=0, r=0, b=0))

        fig.show()

    def draw_scattermatrix(self, data, exp_names, parameters):
        """
        Use data to draw scatter matrix plot
        """

        # sns.set(style="ticks", color_codes=True)

        if self.num_repetitions == 1:
            parameters['config_id'] = {}
            parameters['config_id']['type'] = 'i'
            parameters['config_id']['domain'] = [int(data['config_id'].min()), int(data['config_id'].max())]
            keyParam = 'config_id'
        else:
            parameters['exp_name'] = {}
            parameters['exp_name']['type'] = 'c'
            parameters['exp_name']['domain'] = exp_names
            keyParam = 'exp_name'

        if self.key_param not in ('null', None):
            keyParam = self.key_param
        else:
            keyParam = keyParam 

        dimensions = []
        if self.matrix_param not in (None, 'null'):
            for x in self.matrix_param.split(','):
                dimensions.append(x)
        else:
            dimensions = list(parameters.keys())

        fig = px.scatter_matrix(data,
            dimensions = dimensions,
            color = keyParam,
            title = self.title,
            labels={col:col.replace('_', ' ') for col in data.columns})
        fig.update_traces(diagonal_visible=False)
        fig.show()

    def count_values(self, column):
        data = list(column)
        count = 0
        for x in data:
            if x not in ('null', None):
                count += 1
        return count

