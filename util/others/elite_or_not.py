"""
==============================================================================================

	Version:	1.0
	File:		elites_analysis.py
	Author:		Yunshuang XIAO
	Purpose:	Analyze all the experiment's results from elites
                Check if the best configuration comes from these experiments is as the same
                as the one from crace
	
	INPUT:		DIR_EXP:	the folder of experiment you want to analysis

	OUTPUT:		The proportion of experiments with the same elite
				1 file about the detail of the comparision

==============================================================================================
"""

import argparse
import glob
import json
import os
import sys
import statistics
import re
import math


def check_for_dependencies():
    """
    Check and import all dependent libraries.

    If any required dependency is not installed, stop the script.
    """
    dependency_failed = False
    try:
        global plt  # pylint: disable=global-statement, invalid-name
        import matplotlib.pyplot as plt  # pylint: disable=import-error, import-outside-toplevel
        plt.style.use('ggplot')
    except ModuleNotFoundError:
        print("Matplotlib is a required dependency. You can install it with: ")
        print("$ pip install matplotlib")
        dependency_failed = True
    if dependency_failed:
        print("At least one required dependency was not found. Please install all required dependencies.")
        sys.exit(0)


# def expand_folder_arg(folder_arg):
#     """
#     Runs a glob expansion on the folder_arg elements.
#     Also sorts the returned folders.

#     :param folder_arg:
#     :return:
#     """

#     folder = folder_arg[0]
#     return folder


def load_elite_results(directory):
    """
    Load the results from a list of irace folders

    :param directory: a directory that contains one or multiple runs of irace.
    :param repetitions: the number of repetitions to include. If set to 0, include all repetitions.
    :return:
    """
    
    elite_log_file = directory + "/race_log/test/exps_elite_test200.log"

    test_results = {}
    with open(elite_log_file, "r") as f:
        for line in f:
            line_result = json.loads(line)
            current_id = line_result["configuration_id"]
            current_quality = line_result["quality"]
            if current_id not in test_results.keys():
                test_results[current_id] = []
            test_results[current_id].append(current_quality)
    f.close()
    return test_results

def load_crace_results(directory, best_id: int):
    """
    Load the results from a list of crace folders

    :param directory: a directory that contains one or multiple runs of crace.
    :param repetitions: the number of repetitions to include. If set to 0, include all repetitions.
    :return:
    """
    
    crace_log_file = directory + "/race_log/test/exps_fin.log"
    key_name = "C-%(num)d" % {"num": best_id}

    crace_results = {key_name: []}
    with open(crace_log_file, "r") as f:
        for line in f:
            line_result = json.loads(line)
            current_id = line_result["configuration_id"]
            current_quality = line_result["quality"]
            if current_id == best_id:
                crace_results[key_name].append(current_quality)
    f.close()
    return crace_results

def load_irace_results(directory, best_id: int):
    """
    Load the results from a list of irace folders

    :param directory: a directory that contains one or multiple runs of irace.
    :param repetitions: the number of repetitions to include. If set to 0, include all repetitions.
    :return:
    """
    
    irace_log_file = directory + "/race_log/test/exps_fin.log"
    key_name = "I-%(num)d" % {"num": best_id}

    irace_results = {key_name: []}
    with open(irace_log_file, "r") as f:
        for line in f:
            line_result = json.loads(line)
            current_id = int(line_result["configuration_id"])
            current_quality = int(line_result["quality"])
            if current_id == best_id:
                irace_results[key_name].append(current_quality)
    f.close()
    return irace_results


def log_creat(file):
    f = open(file, "w")
    f.close()


def log_update(file, data):
    with open(file, "a") as f:
        json.dump(data, f)
        f.write("\n")
    f.close()

def log_write(file, data):
    with open(file, "a") as f:
        f.write(data)
    f.close()


def compute_rpd(irace_results, minimum_value):
    """
    :param irace_results:
    :param minimum_value:
    :return:
    """
    if minimum_value is not None:
        if minimum_value == math.inf:
            print(irace_results)
            minimum_value = min([min(x) for _, x in irace_results.items()])
        irace_results = {x: [(y / minimum_value) - 1 for y in irace_results[x]] for x in irace_results}
    print(irace_results)
    return irace_results

def plot_final_elite_results(directory, results, rpd, title, file_name):
    """
    You can either call this method directly or use the command line script (further down).

    :param directory: each separete execution dir
    :param results: a dictionary includes results from crace and new test experiments
    :param title: the title of plot
    :param file_name: the name of output plot file
    :return:
    """
    exp_name = os.path.basename(directory)
    group_name = os.path.basename(os.path.dirname(directory))

    if title:
        file_name = title
    else:
        title = group_name + "_" + exp_name.replace('-', '')

    if rpd is not None:
        results = compute_rpd(results, rpd)
    fig, axis = plt.subplots()  # pylint: disable=undefined-variable
    axis.boxplot(results.values())
    axis.set_xticklabels(results.keys(), rotation=90)
    axis.set_title(title)
    plt.show()  # pylint: disable=undefined-variable

    file_name = title + ".png"
    fig.savefig(directory + "/" + file_name, bbox_inches='tight')

def results_analysis(folder, rpd, plot_title, plot_name, log_name):
    """
    You can either call this method directly or use the command line script (further down).

    :param folder:
    :param rpd
    :param plot_title: the title of each plot
    :param plot_name: the name of each plot file
    :param log_name: the name of output log file
    :return:
    """
    elite_folders = []
    elite_folders = sorted([subdir for subdir, dirs, files in os.walk(folder) \
                    for file in files if file == "exps_elite_test200.log" ])

    output_file = os.path.join(folder, log_name)

    log_creat(output_file)
    
    log_data = {}
    total_num = 0
    same_num = 0
    same_list = []
    for i, folder_name in enumerate(elite_folders):
        flag = False
        exec_dir = os.path.dirname(os.path.dirname(folder_name))
        elite_list = exec_dir + "/elites.log"
        with open(elite_list, "r") as f1:
            elites = f1.readlines()
            pre_elite_id = int(re.sub("\D", "", elites[-1]))
        f1.close()

        elite_results = load_elite_results(exec_dir)

        if os.path.basename(os.path.dirname(exec_dir)) == "irace":
            pre_elite_results = load_irace_results(exec_dir, pre_elite_id)
        else:
            pre_elite_results = load_crace_results(exec_dir, pre_elite_id)
        # plot_data = elite_results.copy()
        # plot_data.update(pre_elite_results)

        # # draw the plot
        # plot_final_elite_results(exec_dir, plot_data, rpd, plot_title, plot_name)

        # elite_results is a dict
        # keys are the configuration_ids, and values are each correspoding qualities
        # what we need is to find out the best id according to the results
        final_results = {}
        for id in elite_results.keys():
            final_results[id] = statistics.mean(elite_results[id])
        best_id = min(final_results, key=lambda x:final_results[x])
        key_name = "N-%(num)d" % {"num": best_id}
        elite_results[key_name] = elite_results.pop(best_id)
        # final_results = {}
        # for id in elite_results.keys():
        #     final_results[id] = statistics.mean(elite_results[id])
        #     print(id, final_results[id])
        # best_id = min(final_results, key=lambda x:final_results[x])
        # print(best_id)

        # sys.exit(1)

        total_num += 1
        if pre_elite_id == best_id:
            same_num += 1
            same_list.append(os.path.basename(os.path.dirname(exec_dir)) + "/" + os.path.basename(exec_dir))
            flag = True

        log_data = {"directory": exec_dir, "status": flag, "best_config_id_crace": pre_elite_id, "real_best_config_id": best_id}
        log_update(output_file, log_data)

        plot_data = elite_results.copy()
        plot_data.update(pre_elite_results)

        # draw the plot
        plot_final_elite_results(exec_dir, plot_data, rpd, plot_title, plot_name)
    
    # comment1 = " In all %(total_num)d experiments, %(same_num)d have the same elite configuration. \n The propotation is %(prop).2f%% " % {"total_num": total_num, "same_num": same_num, "prop": same_num/total_num*100}
    # comment1 = "\nIn all {0} experiments, {1} have the same elite configuration. \nThe propotation is {2:.2f}% \n".format(total_num, same_num, same_num/total_num*100)
    # print(comment1)
    # log_write(output_file, comment1)
    if same_num > 0:
        comment2 = "The experiments have the same elite configuration are: \n"
        log_write(output_file, comment2)
        log_update(output_file, same_list)
    
    


def parse_arguments():
    """
    Parse the command line arguments and return them.
    """
    parser = argparse.ArgumentParser(description="eg: python elites_analysis.py path/to/acotsp")
    parser.add_argument('folder', nargs='+', help="The folder includes a list of experiments from crace")
    parser.add_argument('--title', '-t', default="", help="The title of the plot")
    parser.add_argument('--name', '-n', default="elite_detail", help="The name of the output plot file")
    parser.add_argument("--output", "-o", default="elite_prop.log", help="The name of the output log file")
    parser.add_argument("--relative-difference", "-rpd", nargs='?', type=int, default=None, const=math.inf, dest="rdp",
                        help="The best known quality. If only the flag -rpd is set, "
                             "then the minimum value from the test set will be used.")
    args = parser.parse_args()
    return args


def execute_from_args():
    """
    Parse the command line arguments and plot according to them.
    """
    args = parse_arguments()
    check_for_dependencies()
    folder = args.folder[0]
    results_analysis(folder, args.rdp, args.title, args.name, args.output)


if __name__ == "__main__":
    execute_from_args()
