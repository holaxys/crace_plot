from itertools import combinations
import os
import re
import copy
import math
import sys
import textwrap
import logging

import numpy as np
import pandas as pd
import seaborn as sns
import plotly.graph_objects as go
import ipywidgets as widgets
from IPython.display import display
import matplotlib.pyplot as plt
import scikit_posthocs as sp
import statsmodels.api as sm
import plotly.io as pio

pd.set_option('future.no_silent_downcasting', True)

from scipy import stats
from statannotations.Annotator import Annotator
from statsmodels.formula.api import ols

from crace.errors import OptionError, PlotError
from crace_plot.utils import set_logger

sns.color_palette("vlag", as_cmap=True)
# sns.set_style('white')
# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.width', 1000)

class DrawMethods:
    def __init__(self, options, data, common_dict=None, exp_name=None, elite_ids=None, parameters=None, exp_folder=None, avg=False) -> None:

        self.data = data
        self.exp_names = exp_name
        self.exp_fodler = exp_folder
        if self.exp_fodler:
            self._single = True
        else:
            self._single = False
        self._avg = avg

        self.elite_ids = elite_ids
        self.parameters = parameters

        self.exec_dir = options.execDir.value
        if options.outDir.value == options.outDir.default:
            self.out_dir = common_dict
        else:
            self.out_dir = options.outDir.value

        if exp_folder: self.out_dir = exp_folder

        self.title = options.title.value
        self.file_name = options.fileName.value
        self.save_name = os.path.join(self.out_dir, self.file_name)

        self.key_param = options.keyParameter.value
        self.multi_params = options.multiParameters.value
        self.slice = options.slice.value

        self.confidence = round(options.confidence.value, 2)
        self.alpha = round(1-options.confidence.value, 2)

        self.dpi = options.dpi.value
        self.sf = options.showfliers.value
        self.sm = options.showmeans.value
        self.st = options.statisticalTest.value
        self.so = options.showOrigins.value
        self.sa = options.showAnnotators.value
        self.size = options.size.value

        self.set_layout(self.size)

    def set_layout(self, size):
        if size in ('l', 'large'): column = 1
        elif size in ('s', 'small'): column = 3
        else: column = 2

        if column == 1:
            fig_width = 11.69 
            fig_height = 8.27

        if column in (2,3):
            fig_width = 3.16
            fig_height = 2.24

        margin = 0 
        left_margin = margin / fig_width
        right_margin = 1 - (margin / fig_width)
        top_margin = 1 - (margin / fig_height)
        bottom_margin = margin / fig_height

        self._fig_width = fig_width
        self._fig_height = fig_height

        # large: plot used in one column
        if column == 1:
            sns.set_theme(rc={'figure.figsize':(fig_width,fig_height)}, font_scale=1.3) 
            fontSize = 15
            fliersize = 1.5

        # mid: plots used in double columns
        if column == 2:
            sns.set_theme(rc={'figure.figsize':(fig_width,fig_height)}, font_scale=0.7) 
            fontSize = 7 
            fliersize = .5
        
        # small: plots used in trible columns
        if column == 3:
            sns.set_theme(rc={'figure.figsize':(fig_width,fig_height)}, font_scale=0.9) 
            fontSize = 12
            fliersize = .5

        self._fontSize = fontSize
        self._fliersize = fliersize

        # fig, axis = plt.subplots()  # pylint: disable=undefined-variable
        # fig.subplots_adjust(hspace=0.3, wspace=0.2, bottom=0.2)

class DrawConfigs(DrawMethods):
    def __init__(self, options, data, exp_name, elite_ids, parameters, exp_folder) -> None:
        super().__init__(
            options=options,
            data=data,
            exp_name=exp_name,
            elite_ids=elite_ids,
            parameters=parameters,
            exp_folder=exp_folder)

    def draw_parallelcoord(self):
        """
        Use data to draw a parallel coord plot for the provided Crace results
        """

        num = len(self.data)

        data_new = self.data.copy()

        print("#\n# The original crace results:")
        print(data_new)

        if self.key_param not in ('null', None):
            keyParam = self.key_param
        elif self.slice:
            keyParam = 'slice'
        else:
            keyParam = '.ID'

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
                data_new[name] = data_new[name].map(map_dic[name])

        print("#\n# Replacing NaN values..")
        max_l = max([len(x) for x in new_parameters.keys()])
        col1 = data_new.count() == 0
        for i in range(len(col1)):
            name = col1.index[i]
            if name in new_parameters.keys():
                per = data_new[name].isna().sum() / float(num)
                if per > 0:
                    if new_parameters[name]['type'] != 'c':
                        old = copy.deepcopy(new_parameters[name]['domain'])
                        new_parameters[name]['domain'][1] = old[1]+1
                        # print("! WARNING: 'null/NaN' values in {} has been replaced by {}.".format(name, old[0]-1))
                        data_new[name] = data_new[name].replace('null', old[1]+1)
                        data_new[name] = data_new[name].fillna(old[1]+1)
                    else:
                        old = copy.deepcopy(new_parameters[name]['domain'])
                        new_parameters[name]['domain'].append(len(old))
                        data_new[name] = data_new[name].fillna(len(old))
                        # print("! WARNING: {} has 'null/NaN' values.".format(name))
                    print("#   %*s: old domain %s -> new domain %s " % (max_l, name, old, new_parameters[name]['domain']))
                if col1.iloc[i]:
                    print("! WARNING: all values in {} are NaN, it will be deleted for the plot!".format(name) )
                    new_parameters.pop(col1.index[i])
            else:
                continue

        print("#\n# The new Crace results:")
        print(data_new)

        print("#\n# Elite configurations from the Crace results you provided that will be analysed here:\n# ",
              ', '.join([str(x) for x in self.elite_ids]))

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
        fig.write_image(self.save_name+'.png', width=2560, height=1440)
        print("# {} has been saved in {}.".format(self.file_name+'.png', self.out_dir))

    def draw_parallelcat(self):
        """
        Use data to draw a parallel categorical plot for the provided Crace results
        """
        num = len(self.data)

        data_new = self.data.copy()

        print("#\n# The original crace results:")
        print(data_new)

        new_parameters = copy.deepcopy(self.parameters)

        selected = ['slice']
        if len(self.multi_params) > 0:
            selected.extend(self.multi_params)
        else:
            for x in new_parameters:
                if new_parameters[x]['type'] == 'c':
                    selected.append(x)

        print("#\n# Elite configurations from the Crace results you provided that will be analysed here:\n# ",
              ', '.join([str(x) for x in self.elite_ids]))

        # Create dimensions
        dimensions = []
        for x in selected:
            if x == 'slice':
                dimensions.append(go.parcats.Dimension(
                    values=data_new[x],
                    label=x,
                    categoryorder='category descending',
                ))
            else:
                dimensions.append(go.parcats.Dimension(
                    values=data_new[x],
                    label=x,
                ))

        # Create parcats trace
        color = data_new['slice']
        colorscale = [
            [0.0, '#009392'],
            [0.5, '#F1EAC8'],
            [1.0, '#D0587E']]

        fig = go.Figure(data = [go.Parcats(dimensions=dimensions,
                line={'color': color, 'colorscale': colorscale},
                hoveron='color', hoverinfo='count+probability',
                labelfont={'size': 18},
                tickfont={'size': 16},
                arrangement='freeform')])

        fig.show()
        fig.write_image(self.save_name+'.png', width=2560, height=1440)
        print("# {} has been saved in {}.".format(self.file_name+'.png', self.out_dir))

    def draw_parallelcat_old(self):
        """
        Use data to draw a parallel categorical plot for the provided Crace results
        """

        num = len(self.data)

        data_new = self.data.copy()

        print("#\n# The original crace results:")
        print(data_new)

        if len(self.multi_params) == 0:
            catx = '.ID'
            caty = 'slice'
        else:
            catx = self.multi_params[0]
            caty = self.multi_params[1]

        new_parameters = []
        new_parameters = copy.deepcopy(self.parameters)

        col1 = data_new.count() == 0
        for i in range(len(col1)):
            name = col1.index[i]
            per = data_new[name].isna().sum() / float(num)
            if col1.iloc[i]:
                print("\n! WARNING: all values in {} are NaN, it will be deleted for the plot!".format(name) )
                new_parameters.pop(col1.index[i])
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

        print("#\n# The new Crace results:")
        print(data_new)

        print("#\n# Elite configurations from the Crace results you provided that will be analysed here:\n# ",
              ', '.join([str(x) for x in self.elite_ids]))

        plot_dict = []
        each_dict = {}
        for name in new_parameters.keys():
            if new_parameters[name]['type'] == 'c':
                each_dict = dict(
                    label = name, 
                    values = data_new[name]
                )
                plot_dict.append(each_dict)

        cmin = -0.5
        cmax = 2.5

        color = np.zeros(len(plot_dict), dtype='uint8')
        colorscale = [[0, 'gray'], [0.33, 'gray'],
                    [0.33, 'firebrick'], [0.66, 'firebrick'],
                    [0.66, 'blue'], [1.0, 'blue']]

        # FIXME: cannot update the trace color
        # Build figure as FigureWidget
        fig = go.FigureWidget(data=[
        go.Scatter(
            x = data_new[catx],
            y = data_new[caty],
            marker={'color': color, 'cmin': cmin, 'cmax': cmax,
                    'colorscale': colorscale, 'showscale': True,
                    'colorbar': {'tickvals': [0, 1, 2], 'ticktext': ['None', 'Red', 'Green']}},
            mode='markers',
        ), 
        go.Parcats(
                domain={'y': [0, 0.4]}, 
                dimensions=list([line for line in plot_dict]),
                line={'colorscale': colorscale, 'cmin': cmin, 'cmax': cmax,
                      'color': color, 'shape': 'hspline'}),
        ])

        fig.update_layout(
            height=1000, 
            xaxis={'title': catx},
            yaxis={'title': caty, 'domain': [0.6, 1]},
            dragmode='lasso', 
            hovermode='closest',)

        # Build color selection widget
        color_toggle = widgets.ToggleButtons(
            options=['None', 'Red', 'Blue'],
            index=1, description='Brush Color:', disabled=False)

        # Update color callback
        def update_color(trace, points, state):
            # Compute new color array
            new_color = np.array(fig.data[0].marker.color)
            new_color[points.point_inds] = color_toggle.index

            with fig.batch_update():
                # Update scatter color
                fig.data[0].marker.color = new_color

                # Update parcats colors
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

        print("#\n# The original crace results:")
        print(data)

        print("#\n# Replacing NaN values..")
        max_l = max([len(x) for x in new_parameters.keys()])
        col1 = data.count() == 0
        for i in range(len(col1)):
            name = col1.index[i]
            if name in new_parameters.keys():
                per = data[name].isna().sum() / float(num)
                if per > 0:
                    if new_parameters[name]['type'] != 'c':
                        old = copy.deepcopy(new_parameters[name]['domain'])
                        new_parameters[name]['domain'][1] = old[1]+1
                        # print("! WARNING: 'null/NaN' values in {} has been replaced by {}.".format(name, old[0]-1))
                        data[name] = data[name].replace('null', old[1]+1)
                        data[name] = data[name].fillna(old[1]+1)
                    else:
                        old = copy.deepcopy(new_parameters[name]['domain'])
                        new_parameters[name]['domain'].append(str(len(old)))
                        data[name] = data[name].replace('None', str(len(old)))
                        data[name] = data[name].fillna(str(len(old)))
                        # print("! WARNING: {} has 'null/NaN' values.".format(name))
                    print("#   %*s: old domain %s -> new domain %s " % (max_l, name, old, new_parameters[name]['domain']))
                if col1.iloc[i]:
                    print("! WARNING: all values in {} are NaN, it will be deleted for the plot!".format(name) )
                    new_parameters.pop(col1.index[i])
            else:
                continue

        print("#\n# The new Crace results:")
        print(data)

        subgroup = {}
        for name in new_parameters.keys():
            if name in [".ID", ".PARENT", "slice"]: continue
            subgroup[name] = {}
            subgroup[name]['names'] = []
            subgroup[name]['props'] = []
            if new_parameters[name]['type'] != 'c':
                data[name] = pd.to_numeric(data[name])
                left = min(new_parameters[name]['domain'])
                right1 = max(self.parameters[name]['domain'])
                right2 = max(new_parameters[name]['domain'])
                tmp = (left+right1)/3
                sub1 = '[{:.2f}, {:.2f}]'.format(left, tmp)
                sub2 = '[{:.2f}, {:.2f}]'.format(tmp, 2*tmp)
                sub3 = '[{:.2f}, {:.2f}]'.format(2*tmp, right1)

                subgroup[name]['names'].append(sub1)
                s_bool = ((data[name] >= left) & (data[name] < tmp))
                subgroup[name]['props'].append(int(s_bool.sum()))

                subgroup[name]['names'].append(sub2)
                s_bool = ((data[name] >= tmp) & (data[name] < 2*tmp))
                subgroup[name]['props'].append(int(s_bool.sum()))

                subgroup[name]['names'].append(sub3)
                s_bool = ((data[name] >= 2*tmp) & (data[name] <= right1))
                subgroup[name]['props'].append(int(s_bool.sum()))

                if right1 != right2:
                    subgroup[name]['names'].append('null')
                    s_bool = (data[name] == right2)
                    subgroup[name]['props'].append(int(s_bool.sum()))
                
            else:
                for x in new_parameters[name]['domain']:
                    if x not in self.parameters[name]['domain']:
                        subgroup[name]['names'].append('null')
                    else:
                        subgroup[name]['names'].append(x)
                    s_bool = data[name] == x
                    subgroup[name]['props'].append(int(s_bool.sum()))

        num = len(new_parameters.keys())
        labels = [self.title]
        values = [0]
        parents = [None]
        depths = [0]
        for name in new_parameters.keys():
            if name in [".ID", ".PARENT", "slice"]: continue
            i = 0
            labels.append(name)
            values.append(self.count_values(data[name]))
            parents.append(self.title)
            depths.append(1)
            for i, label in enumerate(subgroup[name]['names']):
                labels.append(label)
                values.append(subgroup[name]['props'][i])
                parents.append(name)
                depths.append(2)

        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            sort=False,
            insidetextorientation='radial',
            textinfo= 'none',
            texttemplate=['%{label}, %{percentEntry:.2%}' if d == 2 else '%{label}' for d in depths],
            maxdepth=-1,
            visible=True,
        ))
        fig.update_layout(margin=dict(t=0, l=0, r=0, b=0),
                          uniformtext=dict(minsize=12, mode='show'))

        fig.show()
        fig.write_html(self.save_name+'.html', full_html=True, include_plotlyjs='cdn')
        print("# {} has been saved in {}.".format(self.file_name+'.html', self.out_dir))

    def draw_pairplot(self):
        """
        Use data to draw scatter matrix plot
        """

        if self.parameters[self.key_param]['type'] != 'c':
            raise OptionError("Key parameter {} must be categorical for drawing pairplot.".format(self.key_param))

        dimensions = []
        if len(self.multi_params) != 0:
            for x in self.multi_params:
                if self.parameters[x]['type'] == 'c':
                    raise OptionError("Selected parameters {} must be numeric.".format(x))
                else:
                    dimensions.append(x)
        else:
            dimensions = list(self.parameters.keys())

        data_new = self.data.copy()

        for name in self.parameters.keys():
            per = data_new[name].isna().sum() / float(len(data_new))
            if per == float(1):
                raise PlotError("All values in {} are 'null', it will be deleted for the plot!".format(name))
            elif per > 0:
                data_new[name].replace('null', np.nan, inplace=True)

        col = data_new.count() == 0
        for i in range(len(col)):
            if col.iloc[i] and col.index[i] in dimensions:
                raise PlotError("All values in {} are NaN, it will be deleted for the plot!".format(col.index[i]))

        sns.set_style('whitegrid')
        fig = sns.pairplot(data=data_new,
                        hue=self.key_param,
                        vars=dimensions,
                        palette="vlag",
                        diag_kind='kde',
                        height=8)

        for ax in fig.axes.flatten():
            if ax is not None:
                name = ax.get_ylabel()
                if name: ax.set_ylim(bottom=min(self.parameters[name]['domain']))

        # plt.suptitle(self.title, size=self._fontSize)
        fig.savefig(self.save_name, dpi=self.dpi)
        print("# {} has been saved in {}.".format(self.file_name+'.png', self.out_dir))

    def draw_histplot(self):
        """
        Use provided data to draw distplot
        """

        sns.set_style('whitegrid')
        sns.set_theme(font_scale=0.9)

        param_names = []
        param_types = []
        if len(self.multi_params) != 0:
            param_names.extend(self.multi_params)
        else:
            for x in self.parameters.keys():
                if x in [".ID", ".PARENT", "slice"]: continue
                param_names.append(x)

        for x in param_names:
            param_types.append(self.parameters[x]['type'])
        
        print("\n# The parameters selected to be visualised: \n#  {}".format(', '.join(param_names)))
        print("\n# The type of selected parameters:  \n#  {}".format(', '.join(param_types)))

        data_new = self.data.copy()

        for name in param_names:
            per = data_new[name].isna().sum() / float(num)
            if per == float(1):
                raise PlotError("All values in {} are 'null', it will be deleted for the plot!".format(name))
            elif per > 0:
                data_new[name].replace('null', np.nan, inplace=True)

        col = data_new.count() == 0
        for i in range(len(col)):
            if col.iloc[i] and col.index[i] in param_names:
                raise PlotError("All values in {} are NaN, it will be deleted for the plot!".format(col.index[i]))

        print("#")

        if not self.slice:
            num = 8
            page_num = math.ceil(len(param_names)/num)
            params = locals()
            file_names = locals()
            start = 0
            for i in range(0, page_num):
                fig, axis = plt.subplots(2, 4, sharey=False, sharex=False)
                plt.subplots_adjust(hspace=0.3, wspace=0.4, bottom=0.2)
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
                                            x=name, stat='percent', kde=True, 
                                            ax=ax)
                            fig = sns.rugplot(data=data_new.sort_values(by=name, na_position='last', ascending=True),
                                            x=name, ax=ax)
                        else:
                            fig = sns.histplot(data=data_new.sort_values(by=name, na_position='last', ascending=True),
                                                x=name, stat='percent', kde=False, 
                                                ax=ax)
                        if len(name) > 25:
                            name = re.sub(r"(.{25})", "\\1\n", name)
                        if column != 0:
                            fig.set_ylabel('')
                        ax.xaxis.set_label_position('top')
                        fig.set_xlabel(name, rotation=0)
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
                
                # plt.suptitle(self.title, size=self._fontSize)
                plot.savefig(save_name, dpi=self.dpi)
                print("# {} has been saved in {}.".format(file_name+'.png', self.out_dir))

        else:
            page_num = len(param_names)
            file_names = locals()
            for i in range(0, page_num):
                if len(self.multi_params) != 1:
                    file_names['plot%s' % i] = self.file_name.split('.')[0]+str(i)
                else:
                    file_names['plot%s' % i] = self.file_name.split('.')[0]
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

                    yticks = ax.get_yticks()
                    ytick_labels = [''] * len(yticks)
                    ytick_labels[1] = str(yticks[1])
                    ax.set_yticks(yticks)
                    ax.set_yticklabels(ytick_labels)

                b,t = fig.get_ylim()
                fig.text(-0.06, 0.6*(t-b)*max_slice, 'Probability', 
                        ha='center', va='center', 
                        rotation='vertical', 
                        transform=ax.transAxes)
                fig.text(1.04, 0.6*(t-b)*max_slice, 'slice', 
                        ha='center', va='center', 
                        rotation='vertical', 
                        transform=ax.transAxes)
                plot = fig.get_figure()
                file_name = file_names['plot%s' % i]
                save_name = os.path.join(self.out_dir, file_name)
                
                # plt.suptitle(self.title, size=self._fontSize)
                plot.savefig(save_name, dpi=self.dpi)
                print("# {} has been saved in {}.".format(file_name+'.png', self.out_dir))

    def draw_boxplot(self):
        """
        Use provided data to draw distplot
        """

        sns.set_style('whitegrid')
        sns.set_theme(font_scale=0.9)

        param_names = []
        param_types = []
        if len(self.multi_params) != 0:
            param_names.extend(self.multi_params)
        else:
            for x in self.parameters.keys():
                if x in [".ID", ".PARENT", "slice"]: continue
                if self.parameters[x]['type'] == 'c': continue
                param_names.append(x)

        for x in param_names:
            param_types.append(self.parameters[x]['type'])
        
        print("\n# The parameters selected to be visualised: \n#  {}".format(', '.join(param_names)))
        print("\n# The type of selected parameters:  \n#  {}".format(', '.join(param_types)))

        data_new = self.data.copy()

        for name in param_names:
            per = data_new[name].isna().sum() / float(num)
            if per == float(1):
                raise PlotError("All values in {} are 'null', it will be deleted for the plot!".format(name))
            elif per > 0:
                data_new[name].replace('null', np.nan, inplace=True)

        col = data_new.count() == 0
        for i in range(len(col)):
            if col.iloc[i] and col.index[i] in param_names:
                raise PlotError("All values in {} are NaN, it will be deleted for the plot!".format(col.index[i]))

        print("#")

        if not self.slice:
            num = 6
            page_num = math.ceil(len(param_names)/num)
            params = locals()
            file_names = locals()
            start = 0
            for i in range(0, page_num):
                fig, axis = plt.subplots(2, 3, sharey=False, sharex=False)
                plt.subplots_adjust(hspace=0.3, wspace=0.2, bottom=0.2)
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
                        fig = sns.boxplot(
                            data=data_new, x=name, y='slice',
                            width=0.5, linewidth=0.5, fliersize=self._fliersize,
                            showfliers=self.sf, showmeans=self.sm,
                            meanprops={"marker": "+",
                                       "markeredgecolor": "black",
                                       "markersize": "8"},
                            orient='h', palette="vlag", hue='slice',
                            legend=False, ax=ax)
                        if len(name) > 25:
                            name = re.sub(r"(.{25})", "\\1\n", name)
                        if column != 0:
                            fig.set_ylabel('')
                        ax.xaxis.set_label_position('top')
                        fig.set_xlabel(name, rotation=0)
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

                # plt.suptitle(self.title, size=self._fontSize)
                plot.savefig(save_name, dpi=self.dpi)
                print("# {} has been saved in {}.".format(file_name+'.png', self.out_dir))
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
                    width=0.5, fliersize=self._fliersize, linewidth=0.5,
                    orient='h', palette="vlag")
                if len(name) > 25:
                    name = re.sub(r"(.{25})", "\\1\n", name)
                if self.title:
                    fig.set_xlabel(self.title)
                else:
                    fig.set_xlabel('')
                fig.set_ylabel('slice', fontsize=self._fontSize)
                fig.tick_params(axis='x', labelsize=self._fontSize)
                fig.tick_params(axis='y', labelsize=self._fontSize)

                plot = fig.get_figure()
                file_name = file_names['plot%s' % i]
                save_name = os.path.join(self.out_dir, file_name)

                # plt.suptitle(self.title, size=self._fontSize)
                plot.savefig(save_name, dpi=self.dpi)
                print("# {} has been saved in {}.".format(file_name+'.png', self.out_dir))

    def draw_heatmap(self):
        """
        Use provided data to draw distplot
        """

        sns.set_style('whitegrid')
        sns.set_theme(font_scale=0.9)

        param_names = []
        if len(self.multi_params) != 0:
            param_names.extend(self.multi_params)

        for x in param_names:
            if self.parameters[x]['type'] != 'c':
                raise OptionError(f"Provided parameter {x} for drawing heatmap should be categorical.")
        
        print("\n# The parameters selected to be visualised: \n#  {}".format(', '.join(param_names)))

        data_new = self.data.copy()
        for name in param_names:
            per = data_new[name].isna().sum() / float(len(data_new))
            if per == float(1):
                print("\n! WARNING: all values in {} are 'null', it will be deleted for the plot!".format(name))
                param_names.pop(param_names.index(name))
            elif per > 0:
                data_new[name] = data_new[name].replace('None', np.nan)
                data_new[name] = data_new[name].fillna(np.nan)

        col = data_new.count() == 0
        for i in range(len(col)):
            if col.iloc[i] and col.index[i] in param_names:
                raise PlotError("All values in {} are NaN, it will be deleted for the plot!".format(col.index[i]))

        print("#")

        if len(param_names) < 2:
            pivot_table = data_new.pivot_table(index='slice', columns=param_names[0], values='.ID', aggfunc='count')
        else:
            pivot_table = data_new.pivot_table(index=param_names[0], columns=param_names[1], values='.ID', aggfunc='count')
        fig = sns.heatmap(pivot_table, annot=True, cmap='PuBu', fmt="g") 
        fig.get_figure().savefig(self.save_name, dpi=self.dpi)
        print("# {} has been saved in {}.".format(self.file_name+'.png', self.out_dir))

    def draw_jointplot(self):
        """
        Use provided data to draw jointplot
        """
        dimensions = []
        if len(self.multi_params) > 0:
            dimensions.extend(self.multi_params)
        key = self.key_param if self.key_param else None
        param_names = dimensions+[key] if key else dimensions
        param_types = []
        for i, x in enumerate(param_names):
            if i == 2 and self.parameters[x]['type'] != 'c':
                raise OptionError(f"Provided key parameter {x} for drawing jointplot must be categorical.")
            if i < 2 and self.parameters[x]['type'] == 'c':
                raise OptionError(f"Provided parameter {x} for drawing jointplot should be categorical.")
            param_types.append(self.parameters[x]['type'])

        print("\n# The parameters selected to be visualised: \n#  {}".format(', '.join(param_names)))
        print("\n# The type of selected parameters:  \n#  {}".format(', '.join(param_types)))

        data = self.data[param_names]

        sns.set_style("white")
        fig = sns.jointplot(
            data=data,
            x=dimensions[0], 
            y=dimensions[1],
            hue=key if key else None,
        )
        fig.fig.set_facecolor('white')
        if key:
            legend = fig.ax_joint.legend(fontsize=self._fontSize*0.6, title_fontsize=self._fontSize*0.7, loc='upper right', bbox_to_anchor=(1, 1))
            legend.set_title(key)
            legend.get_frame().set_alpha(0.5)

        fig.ax_joint.set_facecolor('white')
        fig.ax_marg_x.set_facecolor('white')
        fig.ax_marg_y.set_facecolor('white')
        
        fig.savefig(self.save_name, dpi=self.dpi)
        print("#\n# {} has been saved in {}.".format(self.file_name+'.png', self.out_dir))

    def count_values(self, column):
        data = list(column)
        count = 0
        for x in data:
            if x not in ('null', None):
                count += 1
        return count

class DrawExps(DrawMethods):
    # def __init__(self, options, data, common_dict, elite_ids, num_config) -> None:
    #     super().__init__(options=options, data=data, common_dict=common_dict, elite_ids=elite_ids)
    def __init__(self, options, data, common_dict, elite_ids, num_config, exp_name=None, exp_folder=None, avg=True, paired=False) -> None:
        super().__init__(options=options,
                         data=data,
                         common_dict=common_dict,
                         exp_name=exp_name,
                         elite_ids=elite_ids,
                         exp_folder=exp_folder,
                         avg=avg)
        self._test = options.test.value
        self._paired = paired

        self.save_name = os.path.join(self.out_dir, self.file_name)
        if isinstance(self.elite_ids, dict):
            self.exp_names = list(self.elite_ids.keys())
        elif isinstance(self.elite_ids, list):
            self.exp_names = self.elite_ids
        self.num_config = num_config

    def draw_boxplot(self):
        """
        Use data to draw a boxplot for the top5 elite configurations
        """
        if self._test:
            self.draw_results('boxplot')
        else:
            self.draw_tuning('boxplot')

    def draw_violinplot(self):
        """
        Use data to draw a violin for the top5 elite configurations
        """
        if self._test:
            self.draw_results('violinplot')
        else:
            self.draw_tuning('violinplot')

    def draw_results(self, method):
        """
        draw plot for experiments from the crace test results
        """
        num = self.data['folder'].nunique()
        data = copy.deepcopy(self.data)

        print("# The experiment name(s) of the Crace results you provided:")
        print("#  ", textwrap.fill(re.sub("[\[\]']",'',str(self.exp_names)), width=70))

        print("#\n# The elite configuration ids of each experiment are:")
        ids = re.sub('}','',re.sub('{','',re.sub('\'','',str(self.elite_ids))))
        print("#   {}".format(ids))

        x_lable = 'folder' if len(data['folder'].unique()) > 1 else 'exp_name'
        y_lable = 'avg' if self._avg else 'quality'
        fig = getattr(sns, method)(
            x=x_lable, y=y_lable, data=data, width=0.5,
            showfliers=self.sf, fliersize=self._fliersize,
            linewidth=0.5, palette="vlag", hue=x_lable,
            legend=False,)

        if self.st:
            set_logger('st_log', self._directory + "/" + self._file_name + '.log')
            self.statistic_info(data, self.file_name, fig)

        # show original points
        if self.so:
            fig = sns.stripplot(x='folder', y=y_lable, data=data,
                                color='red', size=2, jitter=True)

        if self.title:
            fig.set_xlabel(self.title)
        else:
            fig.set_xlabel('')

        plot = fig.get_figure()
        # plt.suptitle(self.title, size=self._fontSize)
        plot.savefig(self.save_name, dpi=self.dpi)
        print("#\n# {} has been saved in {}.".format(self.file_name+'.png', self.out_dir))

    def draw_tuning(self, method):
        """
        draw plot for experiments from the crace tuning part
        """
        qualities = copy.deepcopy(self.data[['configuration_id', 'quality']])
        data = copy.deepcopy(self.data)

        results1 = qualities.groupby(['configuration_id']).mean().T.to_dict()
        results2 = self.data.groupby(['configuration_id']).count().T.to_dict()

        results_mean = {}
        results_count = {}

        for id, item in results2.items():
            results_count[int(id)] = None
            results_count[int(id)] = item['instance_id']

        # mean based on Nins, when there is a tie on quality
        for id, item in results1.items():
            results_mean[int(id)] = None
            results_mean[int(id)] = item['quality']
        
        # Sort elite_ids based on results_count values
        #   1. num of instances, increase
        #   2. mean quality, decrease
        results_count_sorted = {k:v for k, v in sorted(results_count.items(), key=lambda x: (x[1], -results_mean[x[0]]), reverse=False)}
        elite_ids_sorted = [int(x) for x in results_count_sorted.keys()]

        min_quality = float("inf")
        best_id = 0
        pairs = [ k for k,v in results_count_sorted.items() if v==max(results_count_sorted.values())]
        for id in pairs:
            if results_mean[int(id)] <= min_quality:
                min_quality = results_mean[int(id)]
                best_id = id
        final_best = self.elite_ids[0]

        elite_labels = []
        for x in elite_ids_sorted:
            if x == best_id and x == final_best:
                x = "±%(num)s" % {"num": x}
            elif x == best_id:
                x = "-%(num)s" % {"num": x}
            elif x == final_best:
                x = "+%(num)s" % {"num": x}
            elite_labels.append(x)

        print("#  (number with +: final elite configuration from crace)")
        print("#  (number with -: configuration having the minimal average value on the most instances)")
        for x in elite_labels:
            int_x = int(re.search(r'\d+', x).group()) if not isinstance(x, int) else x
            print(f"#{x:>12}: ({results_count_sorted[int_x]:>2}, {results_mean[int_x]})", end="\n")

        x_lable = 'configuration_id'
        y_lable = 'quality'

        fig, axis = plt.subplots()  # pylint: disable=undefined-variable
        fig.subplots_adjust(hspace=0.3, wspace=0.2, bottom=0.2)

        # sns.set_style('white')
        # palette = sns.color_palette(["white"], len(elite_labels))
        palette = sns.color_palette("vlag", len(elite_labels))
        # draw the plot
        fig = getattr(sns, method)(
            x=x_lable, y=y_lable, data=data,
            order=elite_ids_sorted, hue=x_lable, legend=False,
            width=.5, showfliers=self.sf, fliersize=self._fliersize,
            showmeans=self.sm,
            meanprops={"marker": "+",
                        "markeredgecolor": "black",
                        "markersize": "8"},
            palette=palette,
            linewidth=1,)
        #     boxprops=dict(edgecolor='black'),
        #     medianprops=dict(color='black'),
        #     whiskerprops=dict(color='black'),
        #     capprops=dict(color='black')
        #     )
        # axis.set_facecolor('white')
        # for spine in axis.spines.values():
        #     spine.set_visible(True)
        #     spine.set_color('black')
        #     spine.set_linewidth(1)
        # axis.grid(False)

        if max(results_count_sorted.values()) <= 30:
            fig = sns.stripplot(
                x=x_lable, y='quality', data=data,
                color='darkred', size=self._fliersize+1, jitter=True)

        # add p-value for the configurations who have the most instances
        if self.st and len(pairs) > 1:
            if (int(final_best) != best_id and 
                int(final_best) in pairs):
                pair = (int(best_id), int(final_best))
            else:
                pair = (int(elite_ids_sorted[-2]), int(elite_ids_sorted[-1]))
            pairs_results = data[data['configuration_id'].isin(pair)].copy()

            pairs_results['configuration_id'] = pairs_results['configuration_id'].astype(int)
            pairs_results['instance_id'] = pairs_results['instance_id'].astype(int)
            pairs_results = pairs_results.sort_values(by=['configuration_id', 'instance_id'], ascending=True)
            pairs_results['configuration_id'] = pairs_results['configuration_id'].astype(int)
            pairs_results['instance_id'] = pairs_results['instance_id'].astype(int)

            # p_values after multiple test correction
            p2 = sp.posthoc_wilcoxon(pairs_results, val_col='quality', group_col='configuration_id',
                                    p_adjust='fdr_bh')
            p2_4 = p2.round(4)

            print("#\n# Adjusted p-values of the last two elite configurations:")
            print(p2_4)

            if self.sa:
                annotator = Annotator(fig, pairs=[pair], data=data, order=elite_ids_sorted, x='configuration_id', y='quality')
                annotator.configure(test='Wilcoxon', text_format='simple', comparisons_correction='fdr_bh',
                                    show_test_name=False, line_width=1, fontsize=self._fontSize)
                annotator.apply_and_annotate()

        # show original points
        if self.so:
            fig = sns.stripplot(x='folder', y=y_lable, data=data,
                                color='red', size=2, jitter=True)

        fig.set_xticks(range(len(elite_labels)))

        if len(elite_labels) > 15:
            fig.set_xticklabels(elite_labels, rotation=90)
        else:
            fig.set_xticklabels(elite_labels, rotation=0)

        if self.title:
            fig.set_xlabel(self.title)
        else:
            fig.set_xlabel('')

        results_count = dict(sorted(results_count.items(), key=lambda x:x[0]))

        # add instance numbers
        _, ymax = axis.get_ylim()
        # xticks = fig.get_xticklabels()
        # xmax, _ = xticks[-1].get_position()
        _, xmax = axis.get_xlim()
        plt.text(x=xmax,y=ymax,s="Nins",ha='right',va='bottom',size=self._fontSize,color='blue')
        i=0
        for x in results_count_sorted.values():
            plt.text(x=i, y=ymax,s=x,ha='center',va='top',size=self._fontSize,color='blue')
            i+=1

        plot = fig.get_figure()
        plot.savefig(self.save_name, dpi=self.dpi)
        print("#\n# {} has been saved in {}.".format(self.file_name+'.png', self.out_dir))

    def statistic_info(self, data, plog, fig):
        ############################# CHECK RESULTS #############################
        #                           Shapiro-Wilk Test                           #
        #                                 LEVENE                                #
        #                                 ANOVA                                 #
        #                         Kruskal-Wallis H Test                         #
        #########################################################################
        l = logging.getLogger('st_log')
        print('\n', data)

        x_lable = 'folder' if len(data['folder'].unique()) > 1 else 'exp_name'
        y_lable = 'avg' if self._avg else 'quality'
        # avg for each folder
        data_groups = [data[y_lable][data[x_lable] == x] for x in data[x_lable].unique()]

        # Shapiro-Wilk Test
        # H0 hypothesis: normality (正态分布)
        shapiro_string = ''
        stat_s = p_s = []
        for x in data[x_lable].unique():
            data_group = data[data[x_lable] == x][y_lable]
            ss, ps = stats.shapiro(data_group)
            stat_s.append(ss)
            p_s.append(ps)
            # print('Shapiro-Wilk Test for folder {}, Statistic: {:.4f}, p-value: {:.4f}'.format(x, stat_s, p_s))
            shapiro_string += 'Shapiro-Wilk Test for folder {}, Statistic: {:.4f}, p-value: {:.4f}\n'.format(x, ss, ps)
        l.debug(f'\nShapiro-Wilk Test - H0 hypothesis: normality ({self.alpha})\n{shapiro_string}')

        # do levene
        # H0 hypothesis: homogeneity of variance (方差齐性)
        stat_l, p_l = stats.levene(*data_groups)
        l.debug(f'\nLevene’s Test - H0 hypothesis: homogeneity of variance ({self.alpha})\n' \
                'stat: {:.4f}, p-value: {:.4f}\n'.format(stat_l, p_l))

        # check the results from Shapiro-Wilk Test and levene
        KW_test = ANOVA_test = False
        if p_l < self.alpha or any(x < self.alpha for x in p_s):
            KW_test = True
        else:
            ANOVA_test = True

        if self._paired:
            grouped = data.groupby(x_lable)
            group_keys = list(grouped.groups.keys())

            group1 = grouped.get_group(group_keys[0])
            group2 = grouped.get_group(group_keys[1])

            merged = pd.merge(
                group1[["instance_id", "quality"]],
                group2[["instance_id", "quality"]],
                on="instance_id",
                suffixes=("_group1", "_group2")
            )

            quality_group1 = merged["quality_group1"]
            quality_group2 = merged["quality_group2"]

            stat_p, p_p = stats.wilcoxon(quality_group1, quality_group2)

            l.debug(f'\nWilcoxon pairwise test - H0 hypothesis: homogeneity of variance ({self.alpha})\n' \
                'stat: {:.4f}, p-value: {:.4f}\n'.format(stat_p, p_p))
            if self.sa:
                # xticks = fig.get_xticks()
                # yticks = fig.get_yticks()
                # print(xticks, yticks)
                # fig.annotate(    
                #     f"p = {p_p:.3f}",
                #     xy=(np.pi / 2, 1), xytext=((xticks[0]+xticks[1])/2, (yticks[0]+yticks[1]/2)),
                #     arrowprops=dict(facecolor="black", arrowstyle="->"),
                #     fontsize=12, color='black')

                ymin, ymax = fig.get_ylim()
                plt.text(x=0.5, y=ymax,
                         s=f"wilcoxon pair-test: p = {p_p:.3f}",
                         ha='center',va='top',
                         size=self._fontSize)
            return

        if ANOVA_test:
            # simulate ANOVA 
            # H0 hypothesis: same mean values
            model = ols(f'{y_lable} ~ C({x_lable})', data=data).fit()
            anova_results = sm.stats.anova_lm(model, typ=2)  # Type 2 ANOVA DataFrame
            l.debug(f'\nANOVA_results - H0 hypothesis: all folders have the same mean values\n{anova_results}')

            ############################# POSTHOC TEST ##############################
            #                           posthoc_wilcoxon                            #
            #########################################################################
            annot_test = 'Wilcoxon'
            try:
                # Wilcoxon signed-rank test
                p1 = sp.posthoc_wilcoxon(data, val_col=y_lable, group_col=x_lable, zero_method='zsplit')
                # p_values after multiple test correction
                p2 = sp.posthoc_wilcoxon(data, val_col=y_lable, group_col=x_lable,
                                        zero_method='zsplit', p_adjust='fdr_bh')
                p2_4 = p2.round(4)
            except Exception as e:
                sys.tracebacklimit = 0
                raise PlotError("posthoc_wilcoxon was failed.")

            l.debug(f"\n############################# Wilcoxon Signed-rank Test ##############################")
            l.debug(f"\nOriginal p_values caculated by 'Wilcoxon':\n{p1}")
            l.debug(f"\nNew p_values corrected by 'fdr_bh':\n{p2}")
            l.debug(f"\nNew rounded p_values:\n{p2_4}")

        if KW_test:
            # do Kruskal-Wallis H
            # H0 hypothesis: same medians
            stat_k, p_k = stats.kruskal(*data_groups)
            l.debug('Kruskal-Wallis Test - H0 hypothesis: all folders have the same medians ({self.alpha})\n' \
                    'Statistic: {:.4f}, p-value: {:.4f}'.format(stat_k, p_k))

            ############################# POSTHOC TEST ##############################
            #                             posthoc_dunn                              #
            #                          posthoc_mannwhitney                          #
            #########################################################################

            # # # Dunn:  
            # p1 = sp.posthoc_dunn(data, val_col=y_lable, group_col=x_lable)
            # # p_values after multiple test correction
            # p2 = sp.posthoc_dunn(data, val_col=y_lable, group_col=x_lable,
            #                         p_adjust='fdr_bh')
            # p2_4 = p2.round(4)

            # l.debug(f"\nOriginal p_values caculated by 'dunn':\n{p1}")
            # l.debug(f"\nNew p_values corrected by 'fdr_bh':\n{p2}")
            # l.debug(f"\nNew rounded p_values:\n{p2_4}")

            annot_test = 'Mann-Whitney'
            try:
                # Mann-Whitney rank-sum test
                p1 = sp.posthoc_mannwhitney(data, val_col=y_lable, group_col=x_lable)
                # p_values after multiple test correction
                p2 = sp.posthoc_mannwhitney(data, val_col=y_lable, group_col=x_lable,
                                        p_adjust='fdr_bh')
                p2_4 = p2.round(4)
            except Exception as e:
                sys.tracebacklimit = 0
                raise PlotError("posthoc_mannwhitney was failed.")
            l.debug(f"\nOriginal p_values caculated by 'mannwhitney (Wilcoxon rank-sum test)':\n{p1}")
            l.debug(f"\nNew p_values corrected by 'fdr_bh':\n{p2}")
            l.debug(f"\nNew rounded p_values:\n{p2_4}")

        ############################# ANNOATE ##############################
        if self.sa:
            order = []
            pairs = []
            p_values = []
            for x in data[x_lable].unique():
                order.append(x)
            i = 0
            for x in order[:-1]:
                i += 1
                for y in order[i:]:
                    pairs.append((x,y))
                    p_values.append(p2.loc[x, y])

            annotator = Annotator(fig, pairs=pairs, order=order,
                                data=data, x=x_lable, y=y_lable)
            annotator.configure(test=annot_test, text_format='star', comparisons_correction='fdr_bh',
                            line_width=.3, fontsize=self._fontSize-2)
            # annotator.apply_and_annotate()

            with open(plog + '.log', 'a') as f1:
                original_stdout = sys.stdout
                sys.stdout = f1
                try:
                    annotator.apply_and_annotate()
                except ValueError as e:
                    sys.tracebacklimit = 0
                    raise PlotError(f"{annot_test} in Annotator was failed.")
                finally:
                    sys.stdout = original_stdout
