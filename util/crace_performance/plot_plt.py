"""
This module provides a set of plotting functions for the race results.
"""

import argparse
import glob
import json
import math
import os
import sys
import statistics
import csv
from collections import Counter


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


def expand_folder_arg(folder_arg):
    """
    Runs a glob expansion on the folder_arg elements.
    Also sorts the returned folders.

    :param folder_arg:
    :return:
    """
    folders = []
    for folder in folder_arg:
        folders.extend(glob.glob(folder))
    return sorted(folders)

def csv_2_log(directory):
    """
    Covert the file named "exps_irace.log" obtained from "R2CSV" 
    to the log format in python crace
    
    :param direvtory
    :return
    """
    path = "./race_log/test/"
    # print("\n==================== Folder arg ====================\n", directory)
    folders = sorted([os.path.join(directory, folder) for folder in os.listdir(directory)
                        if os.path.isdir(os.path.join(directory, folder))])
    for folder_name in folders:
        # print("\n==================== Folder name ====================\n", folder_name)
        log_path = os.path.join(folder_name, path)
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        log_data = {}
        i=0
        with open(folder_name + "/race_log/test/exps_fin.log",'w') as f2:
            with open(folder_name + "/exps_irace.log",'r') as f1:
                for row in csv.reader(f1):
                    if i >= 1:
                        log_data = {"experiment_id": int(row[0]), "configuration_id": int(row[1]), "quality": float(row[2])}
                        # print(log_data)
                        json.dump(log_data,f2)
                        f2.write("\n")
                    i += 1
        # with open(folder_name + "/race_log/test/exps_fin.log",'w') as f2:
            # f2.write(json.dumps(log_data))
        f1.close
        f2.close

        best_data = {}
        i=0
        with open(folder_name + "/race_log/race.log", 'w') as f4:
            with open(folder_name + "/race_irace.log",'r') as f3:
                for row in csv.reader(f3):
                    if i >= 1:
                        # print("row[0]: {}".format(row[0]))
                        best_data = {"best_id": row[0]}
                        json.dump(best_data, f4)
                    i += 1
                    # best_data = {"best_id": row[0]}
                    # print(best_data)
                # json.dump(best_data,f4)
        # with open(folder_name + "/race_log/race.log", 'w') as f4:
            # f4.write(json.dumps(best_data))
            # json.dump(best_data,f4)
        f3.close
        f4.close

def compute_rpd(race_results, minimum_value):
    """
    :param race_results:
    :param minimum_value:
    :return:
    """
    if minimum_value is not None:
        if minimum_value == math.inf:
            print(race_results)
            minimum_value = min([min(x) for _, x in race_results.items()])
        race_results = {x: [(y / minimum_value) - 1 for y in race_results[x]] for x in race_results}
    print(race_results)
    return race_results

def load_race_results(directory, repetitions=0):
    """
    Load the results from a list of race folders

    :param directory: a directory that contains one or multiple runs of race.
    :param repetitions: the number of repetitions to include. If set to 0, include all repetitions.
    :return:
    """

    ## flag = False: ...acotsp/numC/para128_numC1/exp-*
    ##               return result for singel experiment named para128_numC1
    ## flag = True:  ...acotsp/numC/para*
    ##               return result for all experiments in numC named with para*

    flag = False
    race_results = {}

    current_folder=(os.path.split(directory))[-2]+'/'+(os.path.split(directory))[-1]
    # current_folder = directory
    # print("# current folder: ", current_folder)

    if "irace" in current_folder \
        and os.path.exists((glob.glob(directory + r"/*/exps_irace.log"))[0]):
        # print("# current folder: ", current_folder)
        # print(glob.glob(directory + r"/*/exps_irace.log")[0])
        race_folders = sorted([os.path.join(directory, folder) for folder in os.listdir(directory)
                    if os.path.isdir(os.path.join(directory, folder))])
        if not os.path.exists(os.path.join(directory, "race_log/test/exps_fin.log"))  or \
            not os.path.exists(os.path.join(directory, "race_log/race.log")):
            # print("\n==================== Convert csv to logs ====================")
            csv_2_log(directory)
            flag = True

    # if exps_irace.log dose not exist, directory is from crace
    #  check if this folder is the for repetitions or not 
    elif os.path.exists((glob.glob(directory + r"/*/crace.train"))[0]):
        # print(glob.glob(directory + r"/*/exps_crace.log")[0],"\n")
        race_folders = sorted([os.path.join(directory, folder) for folder in os.listdir(directory)
                                if os.path.isdir(os.path.join(directory, folder))])
        # print(crace_folders)
        flag = True

    # results from crace and not for 10 repetitions
    elif os.path.exists(os.path.join(directory, "crace.train")):
        race_folders = sorted([os.path.join(directory, folder) for folder in os.listdir(directory)
                        if os.path.isdir(os.path.join(directory, folder))])
        flag = False
    
    else:
        print("# Error: crace.train cannot be found")
        print("#        input file should be ended with para* or exp*")
        exit()

    # print("\n# curret folder: ", current_folder)
    # print("# crace_folders: ", crace_folders)

    for i, folder_name in enumerate(race_folders):
        if 0 < repetitions <= i:
            break
        if flag:
            test_file_name = folder_name + "/race_log/test/exps_fin.log"
            # print("# folder name: ",folder_name)
        else:
            folder_name = os.path.dirname(folder_name)
            test_file_name = folder_name + "/race_log/test/exps_fin.log"

        with open(folder_name + "/race_log/race.log", "r") as log_file:
            # print("# folder name: ", folder_name)
            race_log = json.load(log_file)
            best_id = int(race_log["best_id"])
        name = folder_name.split("/")[-1]
        test_results = []
        with open(test_file_name, "r") as test_file:
            for line in test_file:
                line_result = json.loads(line)
                if int(line_result["configuration_id"]) == best_id:
                    test_results.append(float(line_result["quality"]))
            race_results[name] = test_results
    return race_results

def plot_performance_variance(folders, repetitions=0, title="", output_filename="plot.png"):
    """
    Plot the variance of independent runs of crace.

    :param folders: a list of folders to be plotted. Each folder should contain one or multiple crace execution folders.
    :param repetitions: the number of repetitions to consider for plotting
    :param title: an optional title for the plot
    :param output_filename: the name for the file to be written to
    :output_filename: the name for the output file. Defaults to "plot.png".
    """
    directory = ""
    if len(folders) == 1:
        directory = folders[0]
    else:
        directory = os.path.dirname(folders[0])
    for folder in folders:
        if os.path.isdir(folder):
            race_results = load_race_results(folder, repetitions)
            fig, axis = plt.subplots()  # pylint: disable=undefined-variable
            axis.boxplot(race_results.values())
            axis.set_xticklabels(race_results.keys(), rotation=90)
            axis.set_title(title)
            # axis.set_facecolor('white')
            # axis.spines['left'].set_color('black')
            # axis.spines['bottom'].set_color('black')
            # axis.spines['top'].set_color('black')
            # axis.spines['right'].set_color('black')
            plt.show()  # pylint: disable=undefined-variable
            # print(os.path.dirname(folders[0]))
            if title:
                output_filename = title + ".png"
            fig.savefig(directory + "/" + output_filename, bbox_inches='tight')


def plot_final_elite_results(folders, rpd, repetitions=0, title="", output_filename="output.png", show: bool = True):
    """
    You can either call this method directly or use the command line script (further down).

    :param folders:
    :param repetitions:
    :param title:
    :param output_filename:
    :return:
    """
    directory = ""
    all_results = {}
    if len(folders) == 1:
        directory = folders[0]
        results = load_race_results(folders[0], repetitions)
        if folders[0].split("/")[-1]:
            all_results[folders[0].split("/")[-1]] = [statistics.mean(results[x]) for x in results]
        else:
            all_results[folders[0].split("/")[-2]] = [statistics.mean(results[x]) for x in results]
    else:
        directory = os.path.dirname(folders[-1])
        names = []
        for folder in folders:
            names.append(os.path.basename(os.path.abspath(os.path.dirname(folder) + os.path.sep + '.')))
        names_count = Counter(names)
        if len(names_count.keys()) > 1:
            for i, folder in enumerate(folders):
                if os.path.isdir(folder):
                    results = load_race_results(folder, repetitions)
                    name = names[i] + '_' + os.path.basename(folder)
                    all_results[name] = [statistics.mean(results[x]) for x in results]
        else:
            # print("# FOLDERS: ", folders)
            for folder in folders:
                if os.path.isdir(folder):
                    results = load_race_results(folder, repetitions)
                    # print("\n# folder: ", folder)
                    # print("# results: ", results)
                    all_results[folder.split("/")[-1]] = [statistics.mean(results[x]) for x in results]
    if rpd is not None:
        all_results = compute_rpd(all_results, rpd)
    fig, axis = plt.subplots()  # pylint: disable=undefined-variable
    if show == True:
        axis.boxplot(all_results.values(), showfliers=True)
    else:
        axis.boxplot(all_results.values(), showfliers=False)
    axis.set_xticklabels(all_results.keys(), rotation=90)
    axis.set_title(title)
    plt.show()  # pylint: disable=undefined-variable
    if title:
        output_filename = title + ".png"
    # axis.set_facecolor('white')
    # axis.spines['left'].set_color('black')
    # axis.spines['bottom'].set_color('black')
    # axis.spines['top'].set_color('black')
    # axis.spines['right'].set_color('black')
    fig.savefig(directory + "/" + output_filename, bbox_inches='tight')

    print("# Plot is saved in folder: ", directory)

def parse_arguments():
    """
    Parse the command line arguments and return them.
    """
    parser = argparse.ArgumentParser(description="eg: python plot_plt.py ~/race/experiments/crace-2.11/acotspqap/qap/numC/para*")
    parser.add_argument('--title', '-t', default="", help="The title of the plot.")
    parser.add_argument('--repetitions', '-r', default=0, type=int, help="The number of repetitions of the experiment")
    parser.add_argument('folder', nargs='+', help="A list of folders to include, supports glob expansion")
    parser.add_argument("--output", '-o', default="plot.png", help="The name of the output file(.png)")
    parser.add_argument("--showfliers", '-s', default=True, help="show fliers or not")
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
    folders = expand_folder_arg(args.folder)
    # plot_performance_variance(folders, args.repetitions, args.title, args.output)
    plot_final_elite_results(folders, args.rdp, args.repetitions, args.title, args.output, args.showfliers)


if __name__ == "__main__":
    execute_from_args()
