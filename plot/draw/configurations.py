import os
import re
import statistics
import sys
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from plot.containers.read_options import ReadOptions
from plot.draw.data import ReadResults

sns.set_theme(rc={'figure.figsize':(11.7,8.27)})

class Configurations:
    """
    Class defines a list of methods used to compare the performance of sampled configurations from Crace
    :ivar exec_dir: the directory of Crace results
    :ivar num_repetitions: the number of repetitions of the provided Crace results
    :ivar title: the title of output plot
    :ivar file_name: the full address and name of the output plot file
    :ivar elitist: analyse the elitist configuration or not
    :ivar all: analyse all configurations or not
    """
    def __init__(self, options: ReadOptions):

        self.exec_dir = options.execDir.value
        self.out_dir = options.outDir.value
        self.num_repetitions = options.numRepetitions.value
        
        self.title = options.title.value
        self.file_name = options.fileName.value

        self.save_name = os.path.join(self.out_dir, self.file_name)

        self.dpi = options.dpi.value
        self.showfliers = options.showfliers.value

        if options.numConfigurations.value == "elites":
            self.num_config = 5
        elif options.numConfigurations.value == "elitist":
            self.num_config = 1
        elif options.numConfigurations.value == "all":
            self.num_config = -5
        elif options.numConfigurations.value == 'allelites':
            self.num_config = -1
        elif options.numConfigurations.value == "else":
            self.num_config = options.elseNumConfigs.value

        self.results_from = options.resultsFrom.value

        self.draw_method = options.drawMethod.value = "boxplot"

        exp_folders = sorted([subdir for subdir, dirs, files in os.walk(self.exec_dir) \
                      for dir in dirs if dir == 'race_log' ])
        print("# Loading Crace results..")
        self.load = ReadResults(exp_folders, options)
        self.all_results, self.exp_names, self.elite_ids = self.load.load_for_configurations()

    def boxplot(self):
        """
        call the function to draw boxplot
        """
        self.draw_boxplot(self.all_results, self.exp_names, self.elite_ids)

    def draw_boxplot(self, elite_results, exp_names, elite_ids):
        """
        Use data to draw a boxplot for the top5 elite configurations
        """

        print("#\n# The Crace results:")
        print(elite_results)
        print("#\n# Elite configurations from the Crace results you provided that will be analysed here :")
        # print("#   ", elite_ids)

        # when drawing plot for the process, num_config is -5 (allelites) or 5 (elites)
        results1 = elite_results.groupby(['config_id']).mean().T.to_dict()
        results2 = elite_results.groupby(['config_id']).count().T.to_dict()
        results_mean = {}
        min_quality = float("inf")
        best_id = 0
        for id, item in results1.items():
            results_mean[int(id)] = None
            results_mean[int(id)] = item['quality']
            if item['quality'] < min_quality:
                min_quality = item['quality']
                best_id = id
        results_count = {}
        for id, item in results2.items():
            results_count[int(id)] = None
            results_count[int(id)] = item['instance_id']

        # mean based on Nins
        # results_mean = {}
        # min_quality = float("inf")
        # max_count = 0
        # best_id = 0
        # for id, item in results1.items():
        #     results_mean[int(id)] = None
        #     results_mean[int(id)] = item['quality']
        #     if item['quality'] <= min_quality and results_count[int(id)] >= max_count:
        #             max_count = results_count[int(id)]
        #             min_quality = item['quality']
        #             best_id = id

        final_best = [x for x in elite_ids if isinstance(x, str)][0]
        
        # Sort elite_ids based on results_count values
        #   1. num of instances, increase
        #   2. mean quality, decrease
        results_count_sorted = {k:v for k, v in sorted(results_count.items(), key=lambda x: (x[1], -results_mean[x[0]]), reverse=False)}
        elite_ids_sorted = [str(x) for x in results_count_sorted.keys()]

        elite_labels = []
        key_name = "-%(num)s-" % {"num": int(best_id)}
        for x in elite_ids_sorted:
            if int(x) == int(best_id):
                x = key_name
            elif int(x) == int(re.search(r'\d+', final_best).group()):
                x = final_best
                if int(re.search(r'\d+', x).group()) == int(best_id):
                    x = "-%(num)s-" % {"num": x}
            elite_labels.append(x)

        print("#   ", elite_labels)

        # draw the plot
        fig, axis = plt.subplots()  # pylint: disable=undefined-variable
        if self.showfliers == True:
            fig = sns.boxplot(x='config_id', y='quality', data=elite_results, \
                              order=elite_ids_sorted, \
                              width=0.5, showfliers=True, fliersize=2,\
                              linewidth=0.5, palette="Set3")
        else:
            fig = sns.boxplot(x='config_id', y='quality', data=elite_results, \
                              order=elite_ids_sorted, \
                              width=0.5, showfliers=False,\
                              linewidth=0.5, palette="Set3")
        fig.set_xticklabels(elite_labels, rotation=0)
        if self.title:
            fig.set_xlabel(self.title)
        else:
            fig.set_xlabel(exp_names)

        results_count = dict(sorted(results_count.items(), key=lambda x:x[0]))

        if self.results_from is None:
            # add instance numbers
            results3 = elite_results.max().T.to_dict()
            max_v = results3['quality'] * 1.0005
            plt.text(x=-0.7,y=max_v,s="ins_num",ha='right',size=10,color='blue')
            i=0
            for x in results_count_sorted.values():
                plt.text(x=i, y=max_v,s=x,ha='center',size=10,color='blue')
                i+=1
        plt.show()

        plot = fig.get_figure()
        plot.savefig(self.save_name, dpi=self.dpi)
        print("#\n# {} has been saved.".format(self.file_name))
