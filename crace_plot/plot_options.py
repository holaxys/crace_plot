import copy
import glob
import os
import sys
import json

import crace.errors as CE
from crace.containers.crace_option import EnablerOption, ListOption
from crace.containers.crace_options import option_decoder
from crace_plot.settings.config import (
    version,
    author,
    author_email,
)

bold = '\033[1m'
underline = '\033[4m'
reset = '\033[0m'

class PlotOptions:
    """
    Class contains the set of options that crace-plot defined for the results analysis.
    The options are defined in a setting file provided by the package.
    The results are record from an exsiting Crace execution.
    """
    def __init__(self, arguments):
        """
        Initialization of an LoadOptions object. Arguments must be provided.

        :param arguments: command line arguments provided by the user (it is not None)
        """
        # TODO: option definition file should be set in the module/package.
        # load options definition from json file
        package_dir, file = os.path.split(__file__)
        filename = package_dir + "/settings/plot_options.json"
        with open(filename, "r") as read_file:
            all_options = json.loads(read_file.read(), object_hook=option_decoder)
        read_file.close()

        # create option variables (default values are put in place)
        self.options = []
        for o in all_options:
            self.options.append(o.name)
            setattr(self, o.name, o)

        # arguments is the whole line of input
        self.arguments = arguments

        # load option values
        try:
            self._load_options(arguments)
            self.check_options()
            self.print_crace_plot_header()
            self.print_options()
        except CE.OptionError as err:
            print("\nERROR: There was an error while reading crace-plot options:")
            print(err)
            sys.tracebacklimit = 0
            raise
        except CE.FileError as err:
            print("\nERROR: There was an error while reading crace-plot options file:")
            print(err)
            sys.tracebacklimit = 0
            raise
        except CE.ExitError:
            sys.tracebacklimit = 0
            raise
        except Exception as err:
            print("\nERROR: There was an error: ")
            print(err)
            sys.tracebacklimit = 7
            raise

    def _load_options(self, arguments):
        """
        Load option values from arguments 

        :param arguments: command line arguments provided by the user (it is not None here)
        :return: none
        """
        # check for help command
        if self.help.long in arguments:
            self.print_help_long()
            raise CE.ExitError("")

        # check for help command
        if self.help.short in arguments:
            self.print_help_short()
            raise CE.ExitError("")

        # check for version command
        if self.version.short in arguments:
            self.print_version_short()
            raise CE.ExitError("")

        if self.version.long in arguments:
            self.print_version_long()
            raise CE.ExitError("")

        if self.man.long in arguments or self.man.short in arguments:
            if self.man.long in arguments:
                index = arguments.index(self.man.long)
            else:
                index = arguments.index(self.man.short)
            if len(arguments) > index+1:
                if arguments[index+1] not in self.options:
                    raise CE.OptionError(f"{arguments[index+1]} is an incorrect crace-plot option name.")
                else:
                    self.print_man(self.get_option(arguments[index+1]))
            else:
                raise CE.OptionError(f"One option shoud be provided for man.")
            raise CE.ExitError("")

        print("# Arguments: {}".format(arguments))
        print("# Loading crace-plot options...")

        options_long = [self.get_option(x).long for x in self.options]
        options_short = [self.get_option(x).short for x in self.options]
        self.arguments = copy.deepcopy(arguments)
        for o in self.options:
            if len(arguments) < 1:
                break
            if self.get_option(o).short in arguments:
                index = arguments.index(self.get_option(o).short)
            elif self.get_option(o).long in arguments:
                index = arguments.index(self.get_option(o).long)
            else:
                continue
        
            if isinstance(self.get_option(o), EnablerOption): 
                self.set_option(o, True)
                del arguments[index]
            elif isinstance(self.get_option(o), ListOption):
                s = []
                start = index
                end = start + 1
                while (end < len(arguments) and 
                       arguments[end] not in options_long and
                       arguments[end] not in options_short):
                    s.append(arguments[end])
                    end += 1
                for i in reversed(range(start, end)):
                    del arguments[i]
                self.set_option(o, s)
            else:
                try:
                    self.set_option(o, arguments[index + 1])
                    del arguments[index:(index + 2)]
                except Exception as e:
                    if isinstance(e, CE.OptionError) or isinstance(e, ValueError):
                        raise CE.OptionError(e)
                    else:
                        raise CE.OptionError(f"{self.get_option(o).name} has no value.")
        if len(arguments) > 0:
            raise CE.OptionError("Argument not recognized: " + arguments[0])

    def check_options(self):
        """
        Checks the crace-plot options are correct
        :return: True if the options are correct
        :raises OptionError: if there is any error in the option values
        """
        # FIXME: check drawMethod options
        # FIXME: check execDir is avaliable or not

        folders = self.expand_folder_arg(self.execDir.value)

        if len(folders) == 0:
            raise CE.PlotError("No crace log files in the provided folder.")
        else:
            self.execDir.set_value(folders)

        if self.dataType.value == "configurations":
            self.drawMethod.value = "boxplot"
            print("When analysing the configurations of the whole procedure, only 'boxplot' can be chosen.")

        if self.dataType.value in ["c", "config", "configs", "configurations"]:
            self.training.set_value(True)
        else:
            if not self.training.value and not self.test.value:
                self.test.set_value(True)

        if self.drawMethod.value is not None and self.execDir.value is None:
            raise CE.ParameterValueError("Option 'execDir' must be provided when 'drawMethod' is not None!")
        elif self.drawMethod.value is None:
            raise CE.ParameterValueError("Option 'drawMethod' must be provided!")
        elif self.title.value is None:        
            path_name1 = os.path.commonpath(folders)
            self.title.value = self.drawMethod.value+': '+path_name1

        if self.drawMethod.value in "(pairplot)" and (self.keyParameter.value is None
            or len(self.keyParameter.value.split(',')) > 1):
            raise CE.ParameterValueError("Parameter 'keyParameter'(-k) must be provided here!")

        if self.drawMethod.value not in "(parallelcoord, piechart, \
            pairplot, histplot, jointplot, boxplot, heatmap)" and self.multiParameters.value is not None:
            raise CE.ParameterValueError("Parameter 'multiParameters'(-m) should not be provided here!")
      
        if self.drawMethod.value in "(jointplot, parallelcat)":
            if self.multiParameters.value is None or len(self.multiParameters.value.split(',')) != 2:
                raise CE.ParameterValueError("When '{}' is called, two parameter names must be provided!".format(self.drawMethod.value))

        if self.drawMethod.value in "(heatmap)":
            if self.multiParameters.value is None or len(self.multiParameters.value.split(',')) > 2:
                raise CE.ParameterValueError("When '{}' is called, one or two parameter names must be provided!".format(self.drawMethod.value))

        if self.statisticalTest.value in (True, "True", "ture") and self.drawMethod.value not in "(boxplot, violinplot)":
            raise CE.ParameterValueError("When '{}' is enable, drawMethod must be in (boxplot, violinplot)!".format(self.statisticalTest.value))

        if self.configurations.value:
            self.configurations.set_value([int(x) for x in self.configurations.value])

    @staticmethod
    def expand_folder_arg(folder_arg):
        """
        Runs a glob expansion on the folder_arg elements.
        Also sorts the returned folders.

        :param folder_arg:
        :return:
        """
        folders = []
        for folder in folder_arg:
            folders.extend([f for f in glob.glob(folder) if os.path.isdir(f)])

        if len(folders) == 0:
            raise CE.ParameterValueError("No crace log files in the provided execDir {}.".format(folder_arg))

        return sorted(folders)

    def get_option(self, option_name):
        """
        get a option in the LoadOption object
        :param option_name: name of the option to be returned
        :return: value of the option
        :raises OptionError: if the option name is unknown
        """
        if option_name not in self.options:
            raise CE.OptionError("Attempt to get unknown option " + option_name)
        return getattr(self, option_name)

    def set_option(self, option_name, option_value):
        """
        set the value of an option in the LoadOptions object
        :param option_name: name of the option
        :param option_value: value to be set
        :return: none
        :raises OptionError: if the option name is unknown
        """
        if option_name not in self.options:
            raise CE.OptionError("Attempt to set unknown option " + option_name + " with value " + option_value)
        getattr(self, option_name).set_value(option_value)

    def is_set(self):
        return not (self.value is None)

    def print_options(self):
        """
        Print all options
        """
        print('# Crace plot options: ')
        for o in self.options:
            if self.get_option(o).critical > 1:
                continue
            if self.get_option(o).type == "e" and self.get_option(o).name not in ['training', 'test']:
                continue
            if self.get_option(o).value in [None, 'none', 'None']:
                continue
            if self.get_option(o).type == "l" and len(self.get_option(o).value) <= 2:
                continue
            v = self.get_option(o).value
            print("#   {}: {}".format(o, v))
        print('#------------------------------------------------------------------------------')

    def print_crace_plot_header(self):
        print('#------------------------------------------------------------------------------')
        print('# crace-plot: An implementation in python of a results analysis for Crace')
        print(f'# Version: {version}')
        print('# Copyright (C) 2023')
        print(f'# {author}    <{author_email}>')
        print('#')
        print('# This is free software, and you are welcome to redistribute it under certain')
        print('# conditions.  See the GNU General Public License for details. There is NO')
        print('# WARRANTY; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.')
        print('#------------------------------------------------------------------------------')

    def print_help_long(self):
        self.print_crace_plot_header()
        package_dir, file = os.path.split(__file__)
        filename = package_dir + "/settings/plot_options.json"
        with open(filename, "r") as read_file:
            all_options = json.loads(read_file.read(), object_hook=option_decoder)

        options = []
        for o in all_options:
            if o.critical > 1:
                continue
            options.append(o.name)
            print("\n# {:<25}{:<5}{:<30}".format(o.name, o.short, o.long))
            if o.default is not None or o.default != "":
                print("  Default: {}".format(o.default))
            if o.type in ['i', 's']:
                print("  Domain: {}".format(o.domain))
            print("  Description: {}".format(o.description))
        print(f'\n# call with {bold}--man [option_name]{reset} to check the details of specified option')
        print('#------------------------------------------------------------------------------')

    def print_help_short(self):
        self.print_crace_plot_header()
        package_dir, file = os.path.split(__file__)
        filename = package_dir + "/settings/plot_options.json"
        with open(filename, "r") as read_file:
            all_options = json.loads(read_file.read(), object_hook=option_decoder)

        options = []
        for o in all_options:
            if o.critical > 1:
                continue
            options.append(o.name)
            print("# {:<25}{:<5}{}".format(o.name, o.short,o.long))
        print(f'\n# call with {bold}--man [option_name]{reset} to check the details of specified option')
        print('#------------------------------------------------------------------------------')

    def print_man(self, o):
        """
        print selected options: critical = 0
        """
        if o.critical > 1 and o.critical <= 4 :
            print(f"Option {o.name} is not available in crace currently.")
            raise CE.ExitError("")
        elif o.critical > 4:
            print(f"{o.name} is not an available crace option.")
            raise CE.ExitError("")

        print(f"{bold}Name:{reset} {o.name}")
        print(f"{bold}Short:{reset} {o.short if o.short else 'None'}")
        print(f"{bold}Long:{reset} {o.long if o.long else 'None'}")
        if o.type in ['i', 's']:
            print(f"{bold}Domain:{reset} {o.domain if o.domain else 'None'}")
        if o.default is not None and o.default != "" and o.default != []:
            print(f"{bold}Default:{reset} {o.default}")
        else:
            print(f"{bold}Default:{reset} None")
        # print(f"{bold}Description:{reset} {o.description if o.description else 'None'}")
        print(f"{bold}Vignettes:{reset} {o.vignettes}")

    def print_version_long(self):
        self.print_crace_header()

    def print_version_short(self):
        print(f"crace {version}")

    def print_all(self):
        """
        Prints all options: critical <= 1
        """
        print("# Scenario options:")
        for o in self.options:
            if self.get_option(o).critical > 1:
                continue
            if self.get_option(o).name != "testType":
                if self.get_option(o).type == "e":
                    continue
                if self.get_option(o).value is None:
                    continue
                if self.get_option(o).type == "l" and len(self.get_option(o).value) <= 2:
                    continue
                # if self.get_option(o).name == "parallel" and self.get_option(o).value >= 3:
                #    self.set_option("mpi", True)
            print("#   " + self.get_option(o).name + ": " + str(self.get_option(o).value))

    def print_selects(self):
        """
        print selected options: critical = 0
        """
        print("# Scenario options:")
        for o in self.options:
            if self.get_option(o).critical > 1:
                continue
            if self.get_option(o).critical == 0:
                if self.get_option(o).type == "e":
                    continue
                if self.get_option(o).value is None:
                    continue
                print("#   " + self.get_option(o).name + ": " + str(self.get_option(o).value))

    @staticmethod
    def print_info():
        print("You can check the information of HELP (-h, --help).")
