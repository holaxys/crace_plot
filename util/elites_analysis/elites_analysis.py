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
import copy

import pandas as pd


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


def load_elite_results(directory, exp_type):
    """
    Load the results from a list of crace folders

    :param directory: a directory that contains one or multiple runs of irace.
    :param repetitions: the number of repetitions to include. If set to 0, include all repetitions.
    :return:
    """
    
    # elite_log_file = directory + "/race_log/test/exps_elite_test200.log"
    if exp_type == 'training':
        elite_log_file = directory + "/race_log/test/exps_elites_train.log"
    elif exp_type == "test":
        elite_log_file = directory + "/race_log/test/exps_elites_test.log"
    else:
        elite_log_file = directory + "/race_log/exps_fin.log"
    
    print("directory: ", directory)
    elites_log = directory + "/elites.log"
    elites_list = []
    with open(elites_log, "r") as f:
        for line in f:
            elites_list.append(int(re.findall(r"\d+",line)[0]))
    f.close()
    elitist_id = elites_list[-1]

    test_results = {}
    with open(elite_log_file, "r") as f:
        for line in f:
            line_result = json.loads(line)
            current_id = str(line_result["configuration_id"])
            current_quality = line_result["quality"]
            if int(current_id) in elites_list:
                # if int(current_id) == elitist_id:
                #     current_id = "-%(num)s-" % {"num": elitist_id}
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
            current_id = line_result["configuration_id"]
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
    return irace_results

def plot_final_elite_results(directory, results, results_count, rpd, title, file_name):
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

    # add instance numbers
    max_v = -9999999.0
    for x in results.keys():
        tm = max(results[x])
        max_v = tm if tm > max_v else max_v
    max_v = max_v * 1.0005
    plt.text(x=-1,y=max_v,s="ins_num",ha='left',size=8,color='blue')
    i=1
    for x in results_count.keys():
        plt.text(x=i, y=max_v,s=results_count[x]['count'],ha='center',size=8,color='blue')
        i+=1

    axis.set_xticklabels(results.keys(), rotation=90)
    axis.set_title(title)
    plt.show()  # pylint: disable=undefined-variable

    file_name = title + ".png"
    fig.savefig(directory + "/" + file_name, bbox_inches='tight')

def results_analysis(folder, rpd, plot_title, plot_name, log_name, exp_type):
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
                    for file in files if file == "exps_fin.log" ])
    test_folders = []
    exp_folders = []
    for x in elite_folders:
        if '/race_log/test' in x:
            test_folders.append(x)
        else:
            exp_folders.append(x)

    elite_folders = copy.deepcopy(exp_folders) if exp_type not in "(training, test)" else \
                    copy.deepcopy(test_folders)

    print(elite_folders)
    output_file = os.path.join(folder, log_name)

    # log_creat(output_file)
    
    log_data = {}
    total_num = 0
    same_num = 0
    same_list = []
    for i, folder_name in enumerate(elite_folders):
        flag = False
        if exp_type in "(training, test)":
            exec_dir = os.path.dirname(os.path.dirname(folder_name))
        else:
            exec_dir = os.path.dirname(folder_name)
        elite_list = exec_dir + "/elites.log"
        with open(elite_list, "r") as f1:
            elites = f1.readlines()
            # pre_elite_id = int(re.sub("\D", "", elites[-1]))
        f1.close()

        elite_results = load_elite_results(exec_dir, exp_type)

        elites = elite_results.keys()
        results_count = {}
        for x in elites:
            results_count[x] = {}
            results_count[x]['mean'] = statistics.mean(elite_results[x])
            results_count[x]['count'] = len(elite_results[x])

        disc_config = []
        for x, value in results_count.items():
            if value['count'] < 5:
                disc_config.append(x)
        if len(disc_config) > 0:
            for x in disc_config:
                del results_count[x] 
                del elite_results[x]

        eval_dict = {x: [r['mean'], -r['count']] for x, r in results_count.items()}

        new = pd.DataFrame(eval_dict, index=["mean", "count"]).transpose()

        cols = ["count", "mean"]
        tups = new[cols].sort_values(cols, ascending=True).apply(tuple, 1)

        f, i = pd.factorize(tups)
        factorized = pd.Series(f + 1, tups.index)

        final = new.assign(Rank=factorized)

        best_id = final["Rank"].idxmin()
        key_name = "*%(num)s*" % {"num": best_id}

        elite_results[key_name] = elite_results.pop(best_id)
        results_count[key_name] = results_count.pop(best_id)

        final_ranks = final["Rank"].to_dict()

        elite_results = sorted(elite_results.items(), key=lambda x:int(re.findall(r"\d+",x[0])[0]))
        
        plot_data = dict(elite_results)

        # draw the plot
        plot_final_elite_results(exec_dir, plot_data, results_count, rpd, plot_title, plot_name)   

        print("# Plot has been saved in folder: ", exec_dir)


def parse_arguments():
    """
    Parse the command line arguments and return them.
    """
    parser = argparse.ArgumentParser(description="eg: python elites_analysis.py path/to/acotsp")
    parser.add_argument('folder', nargs='+', help="The folder includes a list of experiments from crace")
    parser.add_argument('--exp_category', '-c', default="", help="The type of expriments, training or test")
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
    exp_type = args.exp_category
    results_analysis(folder, args.rdp, args.title, args.name, args.output, exp_type)


if __name__ == "__main__":
    execute_from_args()
