import inspect
import os
import re
import copy
import math
import sys
import textwrap
import numpy as np
import pandas as pd
import seaborn as sns
sns.set_theme(rc={'figure.figsize':(11.7,3)})
sns.set_style('white')

import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import scikit_posthocs as sp
from statannotations.Annotator import Annotator

from crace.errors import OptionError

sns.color_palette("vlag", as_cmap=True)
# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.width', 1000)

class DrawMethods:
    def __init__(self, options, data, exp_name=None, elite_ids=None, parameters=None, exp_folder=None, ) -> None:

        self.data = data
        self.exp_names = exp_name
        self.exp_fodler = exp_folder
        self.elite_ids = elite_ids
        self.parameters = parameters

        self.exec_dir = options.execDir.value
        self.out_dir = options.outDir.value
        
        self.title = options.title.value
        self.file_name = options.fileName.value

        self.key_param = options.keyParameter.value
        self.multi_params = options.multiParameters.value
        if self.multi_params is not None and options.drawMethod.value == 'parallelcat':
            self.catx = options.multiParameters.value.split(',')[0]
            self.caty = options.multiParameters.value.split(',')[1]

        self.slice = options.slice.value
        self.dpi = options.dpi.value
        self.showfliers = options.showfliers.value
        self.stest = options.statisticalTest.value

class DrawConfigs(DrawMethods):
    def __init__(self, options, data, exp_name, elite_ids, parameters, exp_folder) -> None:
        super().__init__(options, data, exp_name, elite_ids, parameters, exp_folder)

        if options.outDir.value == options.outDir.default:
            self.out_dir = self.exp_fodler
            self.save_name = os.path.join(self.out_dir, self.file_name)

    def draw_parallelcoord(self):
        """
        Use data to draw a parallel coord plot for the provided Crace results
        """

        num = len(self.data)

        data_new = self.data.copy()
        keyParam = ""

        self.parameters['configuration_id'] = {}
        self.parameters['configuration_id']['type'] = 'i'
        self.parameters['configuration_id']['domain'] = [int(self.data['configuration_id'].min()), int(self.data['configuration_id'].max())]
        keyParam = 'configuration_id'

        if self.key_param not in ('null', None):
            keyParam = self.key_param
        else:
            keyParam = keyParam 

        new_parameters = []
        new_parameters = copy.deepcopy(self.parameters)

        map_dic = {}
        for name in self.parameters.keys():
            if self.parameters[name]['type'] == 'c':
                i = 0
                map_dic[name] = {}
                new_parameters[name]['domain'] = []
                for a in self.parameters[name]['domain']:
                    map_dic[name][a] = i
                    new_parameters[name]['domain'].append(i)
                    i += 1
                data_new[name] = self.data[name].map(map_dic[name])

        col1 = data_new.count() == 0
        for i in range(len(col1)):
            name = col1.index[i]
            per = list(self.data[name]).count('null')/float(num)
            if per > 0:
                if new_parameters[name]['type'] != 'c':
                    old = copy.deepcopy(new_parameters[name]['domain'])
                    new_parameters[name]['domain'][0] = old[0]-1
                    print("! WARNING: 'null' values in {} has been replaced by {}.".format(name, old[0]-1))
                    data_new[name].replace('null', old[0]-1, inplace=True)
                else:
                    old = copy.deepcopy(self.parameters[name]['domain'])
                    new_parameters[name]['domain'].append(len(old))
                    self.parameters[name]['domain'].append('null')
                    print("! WARNING: {} has 'null' values.".format(name))
            if col1[i]:
                print("! WARNING: all values in {} are NaN, it will be deleted for the plot!".format(name) )
                new_parameters.pop(col1.index[i])

        print("#\n# The new self.parameters:")
        print(new_parameters.keys())
        print("#\n# The new Crace results:")
        print(data_new)

        print("#\n# Elite configurations from the Crace results you provided that will be analysed here :")
        for a in self.elite_ids.keys():
            print("#   {}: {}".format(a, self.elite_ids[a]))

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
                    ticktext = self.parameters[name]['domain'],
                    label = name, 
                    values = data_new[name]
                )
            plot_dict.append(each_dict)
        
        cmin = 0
        cmax = 0
        
        if self.parameters[keyParam]['type'] != 'c':
            cmin = self.parameters[keyParam]['domain'][0]
            cmax = self.parameters[keyParam]['domain'][1]
            data_key = pd.to_numeric(data_new[keyParam])
        else:
            cmin = 0
            cmax = len(self.parameters[keyParam]['domain'])
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

    def draw_parallelcat(self):
        """
        Use data to draw a parallel categorical plot for the provided Crace results
        """

        num = len(self.data)

        self.parameters['configuration_id'] = {}
        self.parameters['configuration_id']['type'] = 'i'
        self.parameters['configuration_id']['domain'] = [int(self.data['configuration_id'].min()), int(self.data['configuration_id'].max())]
        keyParam = 'configuration_id'

        new_parameters = []
        new_parameters = copy.deepcopy(self.parameters)

        col1 = self.data.count() == 0
        for i in range(len(col1)):
            name = col1.index[i]
            per = list(self.data[name]).count('null')/float(num)
            if col1[i]:
                print("! WARNING: all values in {} are NaN, it will be deleted for the plot!".format(name) )
                new_parameters.pop(col1.index[i])
            if per > 0:
                if new_parameters[name]['type'] != 'c':
                    old = copy.deepcopy(new_parameters[name]['domain'])
                    new_parameters[name]['domain'][0] = old[0]-1
                    print("! WARNING: 'null' values in {} has been replaced by {}.".format(name, old[0]-1))
                    self.data[name].replace('null', old[0]-1, inplace=True)
                else:
                    old = copy.deepcopy(self.parameters[name]['domain'])
                    new_parameters[name]['domain'].append(len(old))
                    self.parameters[name]['domain'].append('null')
                    print("! WARNING: {} has 'null' values.".format(name))


        print("#\n# The new self.parameters:")
        print(new_parameters.keys())

        print("#\n# Elite configurations from the Crace results you provided that will be analysed here :")
        for a in self.elite_ids.keys():
            print("#   {}: {}".format(a, self.elite_ids[a]))

        plot_dict = []
        each_dict = {}
        for name in new_parameters.keys():
            if new_parameters[name]['type'] == 'c':
                each_dict = dict(
                    label = name, 
                    values = self.data[name]
                )
                plot_dict.append(each_dict)
        
        color = np.zeros(len(plot_dict), dtype='uint8')
        colorscale = [[0, 'gray'], [1, 'firebrick']]
        
        # Build figure as FigureWidget
        fig = go.FigureWidget(data=[
        go.Scatter(
            x = self.data[self.catx],
            y = self.data[self.caty],
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

    def draw_piechart(self):
        """
        Use self.data to draw a pie plot for the provided Crace results
        """

        num = len(self.data)

        data = copy.deepcopy(self.data)
        new_parameters = copy.deepcopy(self.parameters)

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
                    old = copy.deepcopy(self.parameters[name]['domain'])
                    new_parameters[name]['domain'].append(len(old))
                    self.parameters[name]['domain'].append('null')
                    print("! WARNING: {} has 'null' values.".format(name))


        subgroup = {}
        for name in new_parameters.keys():
            subgroup[name] = {}
            subgroup[name]['names'] = []
            subgroup[name]['props'] = []
            if new_parameters[name]['type'] != 'c':
                data[name] = pd.to_numeric(data[name])
                left = self.parameters[name]['domain'][0]
                right = self.parameters[name]['domain'][1]
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
                for x in self.parameters[name]['domain']:
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
            values.append(self.count_values(self.data[name]))
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

    def draw_pairplot(self):
        """
        Use data to draw scatter matrix plot
        """

        # sns.set(style="ticks", color_codes=True)

        if self.parameters[self.key_param]['type'] != 'c':
            raise OptionError("!! keyParam {} must be categorical.".format(self.key_param))

        dimensions = []
        if self.multi_params is not None:
            for x in self.multi_params.split(','):
                if self.parameters[x]['type'] == 'c':
                    raise OptionError("!! keyParam {} must be numeric.".format(x))
                else:
                    dimensions.append(x)
        else:
            dimensions = list(self.parameters.keys())

        data_new = self.data.copy()

        for name in self.parameters.keys():
            per = list(self.data[name]).count('null')/len(self.data)
            if per == float(1):
                print("! WARNING: all values in {} are 'null', it will be deleted for the plot!".format(name))
                dimensions.pop(dimensions.index(name))
            elif per > 0:
                data_new[name].replace('null', np.nan, inplace=True)

        col = data_new.count() == 0
        for i in range(len(col)):
            if col[i] and col.index[i] in dimensions:
                print("! WARNING: all values in {} are NaN, it will be deleted for the plot!".format(col.index[i]) )
                dimensions.pop(dimensions.index((col.index[i])))

        print("#")

        # fig = px.scatter_matrix(data,
        #     dimensions = dimensions,
        #     color = keyParam,
        #     symbol= keyParam,
        #     title = self.title,
        #     labels={col:col.replace('_', ' ') for col in data.columns})
        # fig.update_traces(diagonal_visible=False)
        # fig.show()

        fig = sns.pairplot(data=data_new,
                        hue=self.key_param,
                        vars=dimensions,
                        palette="Set3",
                        diag_kind='kde',
                        height=5)

        # plt.suptitle(self.title, size=15)
        fig.savefig(self.save_name, dpi=self.dpi)
        print("# {} has been saved.".format(self.file_name))

    def draw_histplot(self):
        """
        Use provided data to draw distplot
        """

        sns.set_style('whitegrid')
        sns.set_theme(font_scale=0.9)

        param_names = []
        param_types = []
        if self.multi_params is not None:
            for x in self.multi_params.split(','):
                param_names.append(x)
        else:
            for x in self.parameters.keys():
                # if self.parameters[x]['type'] != 'c':
                param_names.append(x)

        for x in param_names:
            param_types.append(self.parameters[x]['type'])
        
        print("\n# The self.parameters selected to be visualised: \n#  {}".format(param_names))
        print("\n# The type of selected self.parameters:  \n#  {}".format(param_types))

        data_new = self.data.copy()

        for name in self.parameters.keys():
            per = list(self.data[name]).count('null')/len(self.data)
            if per == float(1):
                print("! WARNING: all values in {} are 'null', it will be deleted for the plot!".format(name))
                param_names.pop(param_names.index(name))
            elif per > 0:
                data_new[name].replace('null', np.nan, inplace=True)

        col = data_new.count() == 0
        for i in range(len(col)):
            if col[i] and col.index[i] in param_names:
                print("! WARNING: all values in {} are NaN, it will be deleted for the plot!".format(col.index[i]) )
                param_names.pop(param_names.index((col.index[i])))

        print("#")


        if self.slice not in (True, "true", "True"):
            num = 8
            page_num = math.ceil(len(param_names)/num)
            params = locals()
            file_names = locals()
            start = 0
            for i in range(0, page_num):
                # fig, axis = plt.subplots(1, 3, sharey=False, sharex=False)
                fig, axis = plt.subplots(2, 4, sharey=False, sharex=False)
                plt.subplots_adjust(hspace=0.5, wspace=0.4, bottom=0.2)
                title = '\nPage ' + str(i+1) + ' of ' + str(page_num)
                
                if start+num-1 <= len(param_names):
                    params['params%s' % i] = param_names[start:start+num]
                else:
                    params['params%s' % i] = param_names[start:]              
                start = start+num
                file_names['plot%s' % i] = self.file_name.split('.')[0]+str(i)   

                page_plots = min(num, len(params['params%s' % i]))

                row = column = idx = 0
                for idx in range(num):
                    ax = axis[row, column]
                    if idx < page_plots:
                        name = params['params%s' % i][idx]
                        if self.parameters[name]['type'] != 'c':
                            fig = sns.histplot(data=data_new.sort_values(by=name, na_position='last', ascending=True),
                                            x=name, stat='frequency', kde=True, 
                                            ax=ax)
                            fig = sns.rugplot(data=data_new.sort_values(by=name, na_position='last', ascending=True),
                                            x=name, ax=ax)
                        else:
                            fig = sns.histplot(data=data_new.sort_values(by=name, na_position='last', ascending=True),
                                                x=name, stat='frequency', kde=False, 
                                                ax=ax)
                        if len(name) > 25:
                            name = re.sub(r"(.{25})", "\\1\n", name)
                        if column != 0:
                            fig.set_ylabel('')
                        fig.set_xlabel('\n'+name, rotation=0)
                    else:
                        ax.axis('off')

                    if column < 3:
                        column += 1
                    else:
                        column = 0
                        row += 1 

                plot = fig.get_figure()
                file_name = file_names['plot%s' % i] 
                save_name = os.path.join(self.out_dir, file_name)
                
                plt.suptitle(self.title, size=15)
                plot.savefig(save_name, dpi=self.dpi)
                print("# {} has been saved in {}.".format(file_name, self.out_dir))

        else:
            page_num = len(param_names)
            file_names = locals()
            for i in range(0, page_num):
                file_names['plot%s' % i] = self.file_name.split('.')[0]+str(i)
                name = param_names[i]

                max_slice = max(data_new['slice'])

                fig, axis = plt.subplots(max_slice, 1, sharey=False, sharex=True)

                for j in range(1, max_slice+1):
                    ax = axis[j-1]
                    if self.parameters[name]['type'] != 'c':

                    # statstr
                    # Aggregate statistic to compute in each bin.
                        # count: show the number of observations in each bin
                        # frequency: show the number of observations divided by the bin width
                        # probability or proportion: normalize such that bar heights sum to 1
                        # percent: normalize such that bar heights sum to 100
                        # density: normalize such that the total area of the histogram equals 1

                        fig = sns.histplot(data=data_new[data_new['slice'] == j].sort_values(by=name, na_position='last', ascending=True),
                                        x=name, stat='probability', kde=True, ax=ax)
                        fig = sns.rugplot(data=data_new[data_new['slice'] == j].sort_values(by=name, na_position='last', ascending=True), 
                                        x=name, ax=ax)
                    else:
                        fig = sns.histplot(data=data_new[data_new['slice'] == j].sort_values(by=name, na_position='last', ascending=True),
                                            x=name, stat='probability', kde=False, ax=ax)
                    ax.set_ylabel(f'  {j}', rotation=0)
                    ax.yaxis.set_label_position('right')

                fig.text(-0.1, 5, 'Probability', horizontalalignment='left', verticalalignment='baseline', rotation='vertical', transform=ax.transAxes)
                plot = fig.get_figure()
                file_name = file_names['plot%s' % i]
                save_name = os.path.join(self.out_dir, file_name)
                
                plt.suptitle(self.title, size=15)
                plot.savefig(save_name, dpi=self.dpi)
                print("# {} has been saved in {}.".format(file_name, self.out_dir))

    def draw_boxplot(self):
        """
        Use provided data to draw distplot
        """

        sns.set_style('whitegrid')
        sns.set_theme(font_scale=0.9)

        param_names = []
        param_types = []
        if self.multi_params is not None:
            for x in self.multi_params:
                if self.parameters[x]['type'] != 'c':
                    param_names.append(x)
            if len(param_names) == 0:
                raise OptionError("Required self.parameters must not categorical for boxplot.")
        else:
            for k, i in self.parameters.items():
                if i['type'] != 'c':
                    param_names.append(k)

        for x in param_names:
            param_types.append(self.parameters[x]['type'])
        
        print("\n# The self.parameters selected to be visualised: \n#  {}".format(param_names))
        print("\n# The type of selected self.parameters:  \n#  {}".format(param_types))

        data_new = self.data.copy()

        for name in self.parameters.keys():
            per = list(self.data[name]).count('null')/len(self.data)
            if per == float(1):
                print("! WARNING: all values in {} are 'null', it will be deleted for the plot!".format(name))
                param_names.pop(param_names.index(name))
            elif per > 0:
                data_new[name].replace('null', np.nan, inplace=True)

        col = data_new.count() == 0
        for i in range(len(col)):
            if col.iloc[i] and col.index[i] in param_names:
                print("! WARNING: all values in {} are NaN, it will be deleted for the plot!".format(col.index[i]) )
                param_names.pop(param_names.index((col.index[i])))

        print("#")

        if self.multi_params is None:
            num = 6
            page_num = math.ceil(len(param_names)/num)
            params = locals()
            file_names = locals()
            start = 0
            for i in range(0, page_num):
                fig, axis = plt.subplots(2, 3, sharey=False, sharex=False)
                plt.subplots_adjust(hspace=0.5, wspace=0.4, bottom=0.2)
                title = '\nPage ' + str(i+1) + ' of ' + str(page_num)
                
                if start+num-1 <= len(param_names):
                    params['params%s' % i] = param_names[start:start+num]
                else:
                    params['params%s' % i] = param_names[start:]              
                start = start+num
                file_names['plot%s' % i] = self.file_name.split('.')[0]+str(i)   

                page_plots = min(num, len(params['params%s' % i]))

                row = column = idx = 0
                for idx in range(num):
                    ax = axis[row, column]
                    if idx < page_plots:
                        name = params['params%s' % i][idx]
                        fig = getattr(sns, method)(data=data_new,
                            x=name, y='slice', width=0.5, fliersize=1, linewidth=0.5,
                            orient='h', palette="Set3", ax=ax)
                        if len(name) > 25:
                            name = re.sub(r"(.{25})", "\\1\n", name)
                        if column != 0:
                            fig.set_ylabel('')
                        fig.set_xlabel('\n'+name, rotation=0)
                    else:
                        ax.axis('off')

                    if column < 2:
                        column += 1
                    else:
                        column = 0
                        row += 1 

                plot = fig.get_figure()
                file_name = file_names['plot%s' % i]
                save_name = os.path.join(self.out_dir, file_name)

                plt.suptitle(self.title, size=15)
                plot.savefig(save_name, dpi=self.dpi)
                print("# {} has been saved in {}.".format(file_name, self.out_dir))
        else:
            page_num = len(param_names)
            file_names = locals()
            start = 0
            for i in range(0, page_num):
                plt.clf()
                title = '\nPage ' + str(i+1) + ' of ' + str(page_num)

                file_names['plot%s' % i] = self.file_name.split('.')[0]+'-'+param_names[i]

                name = param_names[i]
                fig = sns.boxplot(data=data_new,
                    x=name, y='slice',
                    hue='slice', legend=False,
                    width=0.5, fliersize=1, linewidth=0.5,
                    orient='h', palette="Set3")
                if len(name) > 25:
                    name = re.sub(r"(.{25})", "\\1\n", name)
                fig.set_xlabel('\n'+name, rotation=0)

                plot = fig.get_figure()
                file_name = file_names['plot%s' % i]
                save_name = os.path.join(self.out_dir, file_name)

                plt.suptitle(self.title, size=15)
                plot.savefig(save_name, dpi=self.dpi)
                print("# {} has been saved.".format(file_name))

    def draw_heatmap(self):
        """
        Use provided data to draw distplot
        """

        sns.set_style('whitegrid')
        sns.set_theme(font_scale=0.9)

        param_names = []
        param_types = []
        for x in self.multi_params.split(','):
            param_names.append(x)

        for x in param_names:
            param_types.append(self.parameters[x]['type'])
        
        print("\n# The self.parameters selected to be visualised: \n#  {}".format(param_names))
        print("\n# The type of selected self.parameters:  \n#  {}".format(param_types))

        data_new = self.data.copy()
        for name in self.parameters.keys():
            per = list(self.data[name]).count('null')/len(self.data)
            if per == float(1):
                print("! WARNING: all values in {} are 'null', it will be deleted for the plot!".format(name))
                param_names.pop(param_names.index(name))
            elif per > 0:
                data_new[name].replace('null', np.nan, inplace=True)

        col = data_new.count() == 0
        for i in range(len(col)):
            if col[i] and col.index[i] in param_names:
                print("! WARNING: all values in {} are NaN, it will be deleted for the plot!".format(col.index[i]) )
                param_names.pop(param_names.index((col.index[i])))

        print("#")

        if len(param_names) < 2:
            pivot_table = data_new.pivot_table(index='slice', columns=param_names[0], values='configuration_id', aggfunc='count')
        else:
            pivot_table = data_new.pivot_table(index=param_names[0], columns=param_names[1], values='configuration_id', aggfunc='count')
        fig = sns.heatmap(pivot_table, annot=True, cmap='PuBu', fmt="g") 
        fig.get_figure().savefig(self.save_name, dpi=self.dpi)
        print("# {} has been saved.".format(self.file_name))

    def draw_jointplot(self):
        """
        Use provided data to draw jointplot
        """

        dimensions = []
        if self.multi_params not in (None, 'null'):
            for x in self.multi_params.split(','):
                if self.parameters[x]['type'] != 'c':
                    dimensions.append(x)
                else:
                    raise OptionError("!!Categorical parameter {} is not supportable here.".format(x))

        data = pd.DataFrame(data=data, columns=dimensions)
        # x=list(map(float, data[dimensions[0]]))
        # y=list(map(float, data[dimensions[1]]))
        x=dimensions[0]
        y=dimensions[1]

        fig = sns.jointplot(
            x=x, 
            y=y,
            data=data,
            kind='hex',
            space=0.1,
            ratio=4)
        
        fig.savefig(self.save_name, dpi=self.dpi)
        print("# {} has been saved.".format(self.file_name))

    def count_values(self, column):
        data = list(column)
        count = 0
        for x in data:
            if x not in ('null', None):
                count += 1
        return count

class DrawExps(DrawMethods):
    def __init__(self, options, data, elite_ids) -> None:
        super().__init__(options=options, data=data, elite_ids=elite_ids)

        self.save_name = os.path.join(self.out_dir, self.file_name)
        self.exp_names = list(self.elite_ids.keys())
        if options.test.value: self.num_config = 1

    def draw_results(self, method):

        num = self.data['folder'].nunique()

        print("\n# The experiment name(s) of the Crace results you provided:")
        print("# ", textwrap.fill(re.sub('\'','',str(self.exp_names)), width=70))

        if self.num_config != 1:
            for i in range(0, num):
                print("#   {}: {}".format(exp_names[i], elite_ids[exp_names[i]]))

            i = 1
            column = 1
            row = 1
            while i < num:
                i += 1
                if num%i == 0 and num/i >= column:
                    row = int(num/i)
                    column = i
            
            fig, axis = plt.subplots(row, column, sharey=True)
            plt.subplots_adjust(hspace=0.3)

            n = 0
            if row > 1:
                for i in range(0, row):
                    for j in range(0, column):
                        data_exp = data.loc[data['exp_name']==exp_names[n]]
                        if self.showfliers == True:
                            fig = getattr(sns, method)(
                                x='configuration_id', y='quality', data=data_exp, width=0.5, fliersize=1, linewidth=0.5, palette="Set2", ax=axis[i,j])
                        else:
                            fig = getattr(sns, method)(
                                x='configuration_id', y='quality', data=data_exp, width=0.5, showfliers=False, linewidth=0.5, palette="Set2", ax=axis[i,j])
                        print(elite_ids[exp_names[n]])
                        fig.set_xticklabels(elite_ids[exp_names[n]], rotation=0, fontsize=10)
                        fig.set_xlabel(exp_names[n])
                        if j != 0:
                            fig.set_ylabel('')
                        n += 1  
            elif num > 1:
                for i in range(0, column):
                    data_exp = data.loc[data['exp_name']==exp_names[n]]
                    if self.showfliers == True:
                        fig = getattr(sns, method)(
                            x='configuration_id', y='quality', data=data_exp, width=0.5, fliersize=1, linewidth=0.5, palette="Set2", ax=axis[i])
                    else:
                        fig = getattr(sns, method)(
                            x='configuration_id', y='quality', data=data_exp, width=0.5, showfliers=False, linewidth=0.5, palette="Set2", ax=axis[i])
                    fig.set_xticklabels(elite_ids[exp_names[n]], rotation=0)
                    fig.set_xlabel(exp_names[n])
                    if i != 0:
                            fig.set_ylabel('')
                    n += 1 
            else:
                if self.showfliers == True:
                    fig = getattr(sns, method)(x='configuration_id', y='quality', data=data, width=0.5, fliersize=2, linewidth=0.5, palette="Set2") 

                else:
                    fig = getattr(sns, method)(x='configuration_id', y='quality', data=data, width=0.5, showfliers=False, linewidth=0.5, palette="Set2") 
                fig.set_xticklabels(elite_ids[exp_names[0]], rotation=0)
                fig.set_xlabel(exp_names[0])

        elif self.num_config == 1:

            ids = re.sub('}','',re.sub('{','',re.sub('\'','',str(elite_ids))))
            print("#   {}".format(ids))

            if self.showfliers == True:
                fig = getattr(sns, method)(x='exp_name', y='quality', data=data)
            else:
                fig = getattr(sns, method)(x='exp_name', y='quality', data=data)

            fig.set_xlabel('\n{}'.format(ids))

        if self.stest in (True, "True", "ture"):
            plog = self.file_name

            # p_values
            p1 = sp.posthoc_wilcoxon(data, val_col='quality', group_col='exp_name')
            # p_values after multiple test correction
            p2 = sp.posthoc_wilcoxon(data, val_col='quality', group_col='exp_name',
                                    p_adjust='fdr_bh')
            print("Original p_values caculated by 'Wilcoxon':\n", p1)
            print("New p_values corrected by 'fdr_bh':\n", p2)

            with open(self.out_dir + "/" + plog + '.log', 'w') as f1:
                print("Original p_values caculated by 'Wilcoxon':\n", p1, file=f1)
                print("\nNew p_values corrected by 'fdr_bh':\n", p2, file=f1)
                print("\n", file=f1)

            order = []
            pairs = []
            p_values = []
            for x in data['exp_name'].unique():
                order.append(x)
            i = 0
            for x in order[:-1]:
                i += 1
                for y in order[i:]:
                    pairs.append((x,y))
                    p_values.append(p2.loc[x, y])

            annotator = Annotator(fig, pairs=pairs, order=order,
                                data=data, x='exp_name', y='quality')
            annotator.configure(test='Wilcoxon', text_format='star', comparisons_correction='fdr_bh',
                                line_width=0.5, fontsize=8)
                                # line_width=1, fontsize=12)
            # annotator.apply_and_annotate()

            with open(self.out_dir + "/" + plog + '.log', 'a') as f1:
                original_stdout = sys.stdout
                sys.stdout = f1

                try:
                    annotator.apply_and_annotate()
                finally:
                    sys.stdout = original_stdout

        
        plot = fig.get_figure()
        plt.suptitle(self.title, size=15)
        plot.savefig(self.save_name, dpi=self.dpi)
        print("# {} has been saved.".format(self.file_name))

    def draw_boxplot(self):
        """
        Use data to draw a boxplot for the top5 elite configurations
        """
        self.draw_results('boxplot')

    def draw_violinplot(self):
        """
        Use data to draw a violin for the top5 elite configurations
        """
        self.draw_results('violinplot')
