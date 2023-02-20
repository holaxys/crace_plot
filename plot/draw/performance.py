import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from plot.containers.read_options import ReadOptions
from plot.draw.data import ReadResults

sns.set(rc={'figure.figsize':(11.7,8.27)})

class Performance:
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

        # self.options = options.options
        # self.arguments = options.arguments
        self.exec_dir = options.execDir.value
        # self.out_dir = options.outDir.value
        # self.drawMethod = options.drawMethod.value
        self.num_repetitions = options.numRepetitions.value
        self.title = options.title.value
        self.file_name = options.fileName.value
        self.num_config = options.numConfigurations.value

        exp_folders = sorted([subdir for subdir, dirs, files in os.walk(self.exec_dir) \
                      for dir in dirs if dir == 'irace_log' ])
        print("# Loading Crace results..")
        self.load = ReadResults(exp_folders)
    
    def boxplot_test(self):
        """
        boxplot on test results
        """

        if self.num_config == 'elites':
            all_results, exp_names, elite_ids = self.load.elite_configs_test()
        elif self.num_config == 'elitist':
            all_results, exp_names, elite_ids = self.load.elitist_test()

        self.draw_boxplot(all_results, exp_names, elite_ids)

    def boxplot_training(self):
        """
        boxplot on training results
        """
        all_results, exp_names, elite_ids = self.load.elite_configs_training()
        self.draw_boxplot(all_results, exp_names, elite_ids)

    def draw_boxplot(self, data, exp_names, elite_ids):
        """
        Use data to draw a boxplot for the top5 elite configurations
        """

        num = self.num_repetitions

        print("#\n# The first 6 lines of the Crace results:")
        print(data.head(6))
        print("# The experiment name(s) of the Crace results you provided:")
        print("# ", exp_names)
        print("# The top5 elite configurations of each repetition from the Crace results you provided:")
        for i in range(0, num):
            print("#   {}: {}".format(exp_names[i], elite_ids[exp_names[i]]))


        i = 1
        column = 1
        row = 1
        while i < num:
            i += 1
            if num%i == 0 and num/i >= column:
                column = int(num/i)
                row = i
        
        fig, axis = plt.subplots(row, column, sharey=True)
        plt.subplots_adjust(hspace=0.3)

        n=0
        if row > 1:
            for i in range(0, row):
                for j in range(0, column):
                    data_exp = data.loc[data['exp_name']==exp_names[n]]
                    print(exp_names[n])
                    fig = sns.boxplot(
                        x='config_id', y='quality', data=data_exp, width=0.5, fliersize=1, linewidth=0.5, palette="Set3", ax=axis[i,j])
                    # fig = sns.swarmplot(
                    #     x='config_id', y='quality', data=data_exp, linewidth=0.5, color=".25", size=1, ax=axis[i,j])
                    fig.set_xticklabels(elite_ids[exp_names[n]], rotation=0, fontsize=10)
                    fig.set_xlabel(exp_names[n])
                    if n != i*column:
                        fig.set_ylabel('')
                    n += 1  
        elif num > 1:
            for i in range(0, column):
                data_exp = data.loc[data['exp_name']==exp_names[n]]
                fig = sns.boxplot(
                    x='config_id', y='quality', data=data_exp, width=0.5, fliersize=1, linewidth=0.5, palette="Set3", ax=axis[i])
                fig.set_xticklabels(elite_ids[exp_names[n]], rotation=0)
                fig.set_xlabel(exp_names[n])
                n += 1
        else:
            fig = sns.boxplot(x='config_id', y='quality', data=data, width=0.5, fliersize=2, linewidth=0.5) 
            fig.set_xticklabels(elite_ids[exp_names[0]], rotation=0)
            fig.set_xlabel(exp_names[0])
        
        plot = fig.get_figure()
        plot.savefig(self.file_name)
