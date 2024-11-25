import copy
import glob
import json
import logging
import os
import sys

import crace
import crace.containers
import crace.containers.parameters
from crace_plot.plot_options import PlotOptions
from crace_plot.draw import DrawExps, DrawConfigs
import numpy as np
import pandas as pd


class ReadCraceResults:
    def __init__(self, options: PlotOptions):
        self.options = options
        self.exec_dir = options.execDir.value
        self.method = options.drawMethod.value

        if options.dataType.value in ["c", "config", "configs", "configurations"]:
            self.data_type = 'c'
        else:
            self.data_type = 'e'

        if self.data_type == 'c' or options.training.value:
            self._single = True
            self.exp_names = []
            self.elites = {}
            self.results = {}
        elif self.data_type == 'e':
            self._single = False
            self.exp_names = {}
            self.elites = {}
            self.results = pd.DataFrame()

        self.exp_folders = []
        for folder in self.exec_dir:
            self.exp_folders.extend(sorted(subdir for subdir, dirs, files in os.walk(folder) \
                                           for dir in dirs if dir == 'race_log' ))
            if not self._single:
                if len(self.exp_folders) == 1: continue
                else:
                    self.exp_folders = list(set(os.path.dirname(x) for x in self.exp_folders))

        self._directory = os.path.commonpath([os.path.abspath(x) for x in self.exec_dir])
        self.parse_num_config()

    def load_data(self):
        """
        """

    def draw_plot(self):
        """
        """

    def parse_slice(self, results, data):
        """
        add slice information to the configuration results
        """
        last_config_ids = results.training.slice['last_config_id'].tolist()
        data['slice'] = pd.NA
        for i, x in enumerate(last_config_ids):
            condition = (data['.ID'] <= x) & (data['slice'].isna())
            data.loc[condition, 'slice'] = i+1
        data.loc[data['slice'].isna(), 'slice'] = len(last_config_ids)+1

    def parse_num_config(self):
        """
        parse the number of configurations from each crace result need to be used for the plot
        """
        if self.options.test.value:
            self._num_config = 1
        else:
            self._num_config = self.options.numConfigurations.value

        if self.options.configurations.is_set():
            self._selected_configs = self.options.configurations.value
        else: self._selected_configs = None

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
        return all_parameters

    def parse_metrics(self, results):
        """
        add metrics id, parent and slice to parameters
        """
        new_params = {}
        for x in ['.ID', '.PARENT', 'slice']:
            new_params[x] = {}
            new_params[x]['type'] = 'i'
            min_d = min(results[x])
            max_d = max(results[x])
            new_params[x]['domain'] = crace.containers.parameters.IntegerParameter.parse_domain(f"({min_d},{max_d})")
        return new_params

class ReadExperiments(ReadCraceResults):
    def __init__(self, options: PlotOptions):
        super().__init__(options)
        self._test = False if options.training.value else True
        self._file_name = options.fileName.value

        self.load_data()
        self.draw_plot()

    def load_data(self):
        """
        load experiments information
        """
        self.exp_names = [os.path.relpath(os.path.abspath(x), self._directory) for x in self.exp_folders]

        if not self._single:
            # load data from multiple results
            avg = {}
            med = {}
            std = {}

            for i, folder in enumerate(self.exp_folders):
                folder_name = self.exp_names[i] if self.exp_names[i] not in ['.', '..'] else \
                    os.path.basename(os.path.abspath(folder))
                exps = sorted(subdir for subdir, dirs, files in os.walk(folder) \
                                for dir in dirs if dir == 'race_log' )
                self.elites[folder_name] = []
                avg[folder_name] = []
                med[folder_name] = []
                std[folder_name] = []
                for exp in exps:
                    tmp_results = crace.crace_cmdline(f'--read, {exp}, --readlogs_in_plot, 1')
                    df = tmp_results.test.data
                    experiments = df[df['configuration_id'] == tmp_results.best_id]

                    avg[folder_name].extend([experiments['quality'].replace([np.inf, -np.inf], np.nan).mean()])
                    med[folder_name].extend([experiments['quality'].replace([np.inf, -np.inf], np.nan).median()])
                    std[folder_name].extend([experiments['quality'].replace([np.inf, -np.inf], np.nan).std()])
                    tmp = pd.DataFrame([[folder_name, os.path.basename(exp), avg[folder_name][-1], med[folder_name][-1], std[folder_name][-1]]], columns=['folder', 'exp_name', 'avg', 'med', 'std'])

                    self.results = pd.concat([self.results, tmp], ignore_index=True)
                    self.elites[folder_name].append(tmp_results.best_id)
            print('#------------------------------------------------------------------------------')

            l = logging.getLogger('st_log')
            filehandler = logging.FileHandler(self._directory + "/" + self._file_name + '.log', mode='w')
            filehandler.setLevel(0)
            streamhandler = logging.StreamHandler()
            l.setLevel(logging.DEBUG)
            l.addHandler(filehandler)
            l.addHandler(streamhandler)

            l.debug(f"# All results:\n{self.results}")
            l.debug(f"\n# All medians: \n{self.results['med'].groupby(self.results['folder']).median().to_string(index=True, header=False)}")
            l.debug(f"\n# All avgs: \n{self.results['avg'].groupby(self.results['folder']).mean().to_string(index=True, header=False)}")
            print('#------------------------------------------------------------------------------')

        else:
            self.exp_names = [os.path.relpath(x, self._directory) for x in self.exp_folders]
            self._tmp_params = {}
            self._all_elites = {}

            for i, folder in enumerate(self.exp_folders):
                name = self.exp_names[i]
                tmp_results = crace.crace_cmdline(f'--read, {folder}, --readlogs_in_plot, 1')
                df = tmp_results.training.data
                self._all_elites[name] = [x[0] for x in tmp_results.training.slice['elites']]

                if self._selected_configs:
                    experiments = df[df['configuration_id'].isin(self._selected_configs)].reset_index(drop=True)
                elif self._num_config != 0:
                    sorted_c = self._all_elites[name].copy()
                    sorted_c.extend([x for x in reversed(list(tmp_results.configurations.all_configurations.keys())) if x not in sorted_c])
                    print(reversed(list(tmp_results.configurations.all_configurations.keys())))
                    experiments = df[df['configuration_id'].isin(sorted_c[:self._num_config])].reset_index(drop=True)
                else:
                    experiments = df[df['configuration_id'].isin(self._all_elites[name])]
                selected = ['experiment_id', 'configuration_id', 'instance_id', 'quality', 'time']
                self.results[name] = experiments[selected].dropna()
                self.results[name]['folder'] = name
                self.results[name]['exp_name'] = name

                self.elites[name] = tmp_results.elites
            print('#------------------------------------------------------------------------------')

    def draw_plot(self):
        """
        draw plot for experiments
        """
        print("# Drawing plot for configurations: \n#")
        try:
            if not self._single:
                self.de = DrawExps(options=self.options,
                                    data=self.results,
                                    common_dict=self._directory,
                                    elite_ids=self.elites,
                                    num_config=self._num_config)
                getattr(self, self.method)()
                print('#------------------------------------------------------------------------------')
            else:
                for i, folder in enumerate(self.exp_folders):
                    name = self.exp_names[i]
                    configs = self.results[name]['configuration_id'].unique().tolist()
                    self.de = DrawExps(options=self.options,
                                        data=self.results[name],
                                        common_dict=self._directory,
                                        exp_name=name,
                                        elite_ids=self.elites[name],
                                        exp_folder=os.path.abspath(folder),
                                        num_config=len(configs))
                    print(f"# {i+1}. {os.path.abspath(folder)}")
                    getattr(self, self.method)()
                    print('#------------------------------------------------------------------------------')
        except Exception as e:
            print("ERROR: There was an error when drawing plot for experiments:")
            print(e)
            sys.tracebacklimit = 12
            raise e

    def boxplot(self):
        """
        call the function to draw boxplot
        """
        self.de.draw_boxplot()

    def violinplot(self):
        """
        call the function to draw violinplot
        """
        self.de.draw_violinplot() 

class ReadConfigurations(ReadCraceResults):
    def __init__(self, options: PlotOptions):
        super().__init__(options)

        self.load_data()
        self.draw_plot()

    def load_data(self):
        """
        load configuration information
        """
        self.exp_names = [os.path.relpath(x, self._directory) for x in self.exp_folders]
        self._tmp_params = {}

        for i, folder in enumerate(self.exp_folders):
            name = self.exp_names[i]
            tmp_results = crace.crace_cmdline(f'--read, {folder}, --readlogs_in_plot, 1')
            df = tmp_results.configurations.print_all().kwargs['all']
            if self._selected_configs:
                # only selected configurations
                configurations = df[df['.ID'].isin(self._selected_configs)].reset_index(drop=True)
            elif self._num_config != 0:
                # a number of configurations
                # elites are ranked at the top
                sorted_c = tmp_results.elites.copy()
                sorted_c.extend([x for x in reversed(list(tmp_results.configurations.all_configurations.keys())) if x not in sorted_c])
                print(reversed(list(tmp_results.configurations.all_configurations.keys())))
                configurations = df[df['.ID'].isin(sorted_c[:self._num_config])].reset_index(drop=True)
            else:
                # all configurations
                configurations = df
            self.results[name] = configurations
            self.elites[name] = tmp_results.elites

            self.parse_slice(tmp_results, self.results[name])
            self._tmp_params[name] = self.parse_metrics(self.results[name])
        print('#------------------------------------------------------------------------------')

        self.parameters = self.parse_parameters(tmp_results.parameters)
        print("# Parameters of the provided scenario:")
        max_l = max([len(x) for x in self.parameters.keys()])
        for k,v in self.parameters.items():
            value = ', '.join(f'{m}: {n}' for m, n in v.items())
            print("#   %*s: %s" % (max_l, k, value))
        print('#------------------------------------------------------------------------------')

    def draw_plot(self):
        """
        draw plot for configurations
        """
        print("# Drawing plot for configurations: \n#")
        for i, folder in enumerate(self.exp_folders):
            try:
                name = self.exp_names[i]
                merged_dict = {**self._tmp_params[name], **self.parameters}

                self.dc = DrawConfigs(options=self.options,
                                    data=self.results[name],
                                    exp_name=name,
                                    elite_ids=self.elites[name],
                                    parameters=merged_dict,
                                    exp_folder=os.path.abspath(folder))
                print(f"# {i+1}. {os.path.abspath(folder)}")
                getattr(self, self.method)()
                print('#------------------------------------------------------------------------------')
            except Exception as e:
                print("ERROR: There was an error when drawing plot for configurations:")
                print(e)
                sys.tracebacklimit = 12
                raise e

    def parallelcoord(self):
        """
        call the function to draw parallel coord plot
        """
        self.dc.draw_parallelcoord()

    def parallelcat(self):
        """
        call the function to draw parallel categorical plot
        """
        self.dc.draw_parallelcat()

    def piechart(self):
        """
        call the function to draw pie chart
        """
        self.dc.draw_piechart()

    def pairplot(self):
        """
        call the function to draw scatter matrix plot
        """
        self.dc.draw_pairplot()

    def histplot(self):
        """
        call the function to draw distplot
        """
        self.dc.draw_histplot()

    def boxplot(self):
        """
        call the function to draw distplot
        """

        self.dc.draw_boxplot()

    def heatmap(self):
        """
        call the function to draw distplot
        """
        self.dc.draw_heatmap()

    def jointplot(self):
        """
        call the function to draw jointplot
        """
        self.dc.draw_jointplot()
