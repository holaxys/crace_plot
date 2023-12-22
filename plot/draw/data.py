import json
import os
import re
import sys
import pandas as pd

from plot.containers.read_options import ReadOptions
from plot.errors import OptionError

class ReadResults:
    def __init__(self, folders, options: ReadOptions):
        """
        Read Crace results from execDir

        :param num_repetitions: the number of repetitions of Crace in the given directory
        :param exec_dir: the directory stored Crace results
        """
        self.folders = folders
        self.dataFrom = options.dataFrom.value

        self.elite_log = "race_log/elite.log"
        self.config_log = "race_log/config.log"
        self.params = "race_log/parameters.log"
        self.all_elites = "elites.log"
        self.exps_fin = ""

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

        self.config_type = options.configType.value

        # select exact way to load Crace results via :param{drawMethod}
        # e.g.: heatmap for config_data; boxplot for performance
        self.draw_method = options.drawMethod.value

    def load_for_perfomance(self):
        """
        Read elite configurations (the best or the top 5 ) in Crace training results
        Tips: the quality of each experiments on different configurations
        """

        self.exps_fin = "race_log/exps_fin.log" if self.config_type == "training" else "race_log/test/exps_fin.log"

        if self.num_config > 0:
            all_data, exp_names, elite_ids = self.elitist_quality() if self.num_config == 1 else self.elites_quality()
            return all_data, exp_names, elite_ids
    
    def load_for_configurations(self):
        """
        Read configurations (the best or the top 5 ) in Crace results
        Tips: the value of parameters for each configuration
        """

        self.parameters = self.parse_parameters()

        if self.num_config == 1:
            all_configs, config_ids, elite_ids = self.elitist_config() 
        elif self.num_config == 5:
            all_configs, config_ids, elite_ids = self.elite_configs()
        elif self.num_config == -1:
            all_configs, config_ids, elite_ids = self.all_elite_configs()
        elif self.num_config == -5:
            all_configs, config_ids, elite_ids = self.all_configs()
        else:
            all_configs, config_ids, elite_ids = self.else_configs()
        
        return all_configs, config_ids, elite_ids, self.parameters

    def load_for_process(self):
        """
        Read configurations (all the elitist or the final 5 ) in Crace results
        Tips: the quality of each configuration
        """

        if self.config_type == "training":
            # all elite configurations run on the whole training instances 
            self.exps_fin = "race_log/test/exps_elites_train.log" 
        elif self.config_type == "test":
            # all elite configurations run on the whole test instances
            self.exps_fin = "race_log/test/exps_elites_test.log" 
        else:
            # all elite configurations from the process
            self.exps_fin = "race_log/exps_fin.log"

        if self.num_config == 5:
            all_data, config_ids, elite_ids = self.elites_process()
        elif self.num_config == -1:
            all_data, config_ids, elite_ids = self.all_elite_process()
        else:
            raise OptionError("The parameter 'num-configurations' can only be 'elites' or 'allelites'.")

        return all_data, config_ids, elite_ids

    def elites_quality(self):
        """
        Read Crace results of the at most top5 elite configurations
        """

        all_data = pd.DataFrame()
        exp_names = []
        elite_ids = {}

        for folder in self.folders:
            name = os.path.basename(folder)
            exp_names.append(name)
            elite_ids[name] = []
            i = 0
            with open(os.path.join(folder, self.elite_log), "r") as f1:
                for line in f1:
                    if i > 0 and i <= self.num_config:
                        elite_id = int(line.split(',')[-2])
                        elite_ids[name].append(elite_id)
                    i += 1
            f1.close()
            tmp = pd.DataFrame()
            with open(os.path.join(folder, self.exps_fin), "r") as f2:
                for line in f2:
                    line_results = json.loads(line)
                    current_id = int(line_results["configuration_id"])
                    current_quality = float(line_results["quality"])
                    if current_id in elite_ids[name]:
                        tmp = pd.DataFrame([[name, current_id, current_quality]], columns=['exp_name', 'config_id', 'quality'])
                        all_data = pd.concat([all_data, tmp], ignore_index=True)
            f2.close
        return all_data, exp_names, elite_ids
        
    def elitist_quality(self):
        """
        Read Crace results for only the best configuration
        """
        all_data = pd.DataFrame()
        exp_names = []
        elitist_ids = {}
        elitist_ids['elitist'] = []
        elite_ids = {}

        for folder in self.folders:
            name = os.path.basename(folder)
            exp_names.append(name)
            elite_ids[name] = []
            i = 0
            with open(os.path.join(folder, self.elite_log), "r") as f1:
                for line in f1:
                    if i > 0 and i <= self.num_config :
                        elite_id = int(line.split(',')[-2])
                        elitist_ids['elitist'].append(elite_id)
                        elite_ids[name].append(elite_id)
                    i += 1
            f1.close()
            tmp = pd.DataFrame()
            with open(os.path.join(folder, self.exps_fin), "r") as f2:
                for line in f2:
                    line_results = json.loads(line)
                    current_id = int(line_results["configuration_id"])
                    current_quality = float(line_results["quality"])
                    if current_id in elite_ids[name]:
                        tmp = pd.DataFrame([[name, current_id, current_quality]], columns=['exp_name', 'config_id', 'quality'])
                        all_data = pd.concat([all_data, tmp], ignore_index=True)
            f2.close

        return all_data, exp_names, elitist_ids

    def elite_configs(self):
        """
        Read the at least top 5 configurations from the provided Crace results
        """

        # parameters need to be returned
        all_configs = pd.DataFrame()
        exp_names = []
        elite_ids = {}

        for folder in self.folders:
            name = os.path.basename(folder)
            exp_names.append(name)
            elite_ids[name] = []
            config_ids = []
            i = 0
            # read elite_log file to get the elitist configuration id
            with open(os.path.join(folder, self.elite_log)) as f1:
                for line in f1:
                    if i > 0 and i <= self.num_config:
                        elite_id = int(line.split(',')[-2])
                        elite_ids[name].append(elite_id)
                    i += 1
            f1.close()

            tmp = t1 = t2 = pd.DataFrame()
            # read config_log file to get the details of each elitist configuration 
            with open(os.path.join(folder, self.config_log), 'r') as f2:
                for line in f2:
                    config_id = int(line.split(',')[0])
                    if config_id not in config_ids and config_id in elite_ids[name]:
                        config_ids.append(config_id)
                        params = re.sub('"','',line.split('{')[1].split('}')[0])
                        t1 = pd.DataFrame([config_id], columns=['config_id'])
                        t2 = pd.DataFrame([name], columns=['exp_name'])
                        for pa in params.split(', '):
                            param_name = pa.split(': ')[0]
                            param_value = pa.split(': ')[1]
                            if 'i' in self.parameters[param_name]['type'] and param_value not in (None, 'null'):
                                param_value = int(pa.split(': ')[1])
                            elif 'r' in self.parameters[param_name]['type'] and param_value not in (None, 'null'):
                                param_value = float(pa.split(': ')[1])
                            tmp = pd.DataFrame([param_value], columns=[param_name])
                            t1 = pd.concat([t1, tmp], axis=1)
                        t2 = pd.concat([t2, t1], axis=1)
                        all_configs = pd.concat([all_configs, t2], ignore_index=True)
            f2.close()    

        return all_configs, exp_names, elite_ids

    def all_elite_configs(self):
        """
        Read the at least top 5 configurations from the provided Crace results
        """

        # parameters need to be returned
        all_configs = pd.DataFrame()
        exp_names = []
        elite_ids = {}

        for folder in self.folders:
            name = os.path.basename(folder)
            exp_names.append(name)
            elite_ids[name] = []
            config_ids = []
            i = 0
            # read elites.log file to get the elitist configuration id
            with open(os.path.join(folder, self.all_elites), "r") as f1:
                for line in f1:
                    elite_ids[name].append(int(re.sub("\D", "", line)))
            f1.close()
            elite_ids[name].pop()

            tmp = t1 = t2 = pd.DataFrame()
            # read config_log file to get the details of each elitist configuration 
            with open(os.path.join(folder, self.config_log), 'r') as f2:
                for line in f2:
                    config_id = int(line.split(',')[0])
                    if config_id not in config_ids and config_id in elite_ids[name]:
                        config_ids.append(config_id)
                        params = re.sub('"','',line.split('{')[1].split('}')[0])
                        t1 = pd.DataFrame([config_id], columns=['config_id'])
                        t2 = pd.DataFrame([name], columns=['exp_name'])
                        for pa in params.split(', '):
                            param_name = pa.split(': ')[0]
                            param_value = pa.split(': ')[1]
                            if 'i' in self.parameters[param_name]['type'] and param_value not in (None, 'null'):
                                param_value = int(pa.split(': ')[1])
                            elif 'r' in self.parameters[param_name]['type'] and param_value not in (None, 'null'):
                                param_value = float(pa.split(': ')[1])
                            tmp = pd.DataFrame([param_value], columns=[param_name])
                            t1 = pd.concat([t1, tmp], axis=1)
                        t2 = pd.concat([t2, t1], axis=1)
                        all_configs = pd.concat([all_configs, t2], ignore_index=True)
            f2.close()    

        return all_configs, exp_names, elite_ids

    def elitist_config(self):
        """
        Read the best configuration from the provided Crace results
        """

        # parameters need to be returned
        all_configs = pd.DataFrame()
        exp_names = []
        elite_ids = {}
        elitist_ids = {}
        elitist_ids['elitist'] = []

        for folder in self.folders:
            name = os.path.basename(folder)
            exp_names.append(name)
            elite_ids[name] = []
            config_ids = []
            i = 0
            # read elite_log file to get the elitist configuration id
            with open(os.path.join(folder, self.elite_log)) as f1:
                for line in f1:
                    if i == 1:
                        elite_id = int(line.split(',')[-2])
                        elite_ids[name].append(elite_id)
                        elitist_ids['elitist'].append(elite_id)
                    i += 1
            f1.close()

            # read config_log file to get the details of each elitist configuration 
            tmp = t1 = t2 = pd.DataFrame()
            with open(os.path.join(folder, self.config_log), 'r') as f2:
                for line in f2:
                    config_id = int(line.split(',')[0])
                    if config_id not in config_ids and config_id in elite_ids[name]:
                        config_ids.append(config_id)
                        params = re.sub('"','',line.split('{')[1].split('}')[0])
                        t1 = pd.DataFrame([config_id], columns=['config_id'])
                        t2 = pd.DataFrame([name], columns=['exp_name'])
                        for pa in params.split(', '):
                            param_name = pa.split(': ')[0]
                            param_value = pa.split(': ')[1]
                            if 'i' in self.parameters[param_name]['type'] and param_value not in (None, 'null'):
                                param_value = int(pa.split(': ')[1])
                            elif 'r' in self.parameters[param_name]['type'] and param_value not in (None, 'null'):
                                param_value = float(pa.split(': ')[1])
                            tmp = pd.DataFrame([param_value], columns=[param_name])
                            t1 = pd.concat([t1, tmp], axis=1)
                        t2 = pd.concat([t2, t1], axis=1)
                        all_configs = pd.concat([all_configs, t2], ignore_index=True)
            f2.close()

        return all_configs, exp_names, elitist_ids

    def all_configs(self):
        """
        Read the at least top 5 configurations from the provided Crace results
        """

        # parameters need to be returned
        all_configs = pd.DataFrame()
        exp_names = []
        elite_ids = {}

        for folder in self.folders:
            name = os.path.basename(folder)
            exp_names.append(name)
            elite_ids[name] = []
            config_ids = []
            i = 0
            # read elite_log file to get the elitist configuration id
            with open(os.path.join(folder, self.elite_log)) as f1:
                for line in f1:
                    if i > 0 and i <= 5:
                        elite_id = int(line.split(',')[-2])
                        elite_ids[name].append(elite_id)
                    i += 1
            f1.close()

            tmp = t1 = t2 = pd.DataFrame()
            # read config_log file to get the details of each elitist configuration 
            with open(os.path.join(folder, self.config_log), 'r') as f2:
                for line in f2:
                    config_id = int(line.split(',')[0])
                    if config_id not in config_ids:
                        config_ids.append(config_id)
                        params = re.sub('"','',line.split('{')[1].split('}')[0])
                        t1 = pd.DataFrame([config_id], columns=['config_id'])
                        t2 = pd.DataFrame([name], columns=['exp_name'])
                        for pa in params.split(', '):
                            param_name = pa.split(': ')[0]
                            param_value = pa.split(': ')[1]
                            if 'i' in self.parameters[param_name]['type'] and param_value not in (None, 'null'):
                                param_value = int(pa.split(': ')[1])
                            elif 'r' in self.parameters[param_name]['type'] and param_value not in (None, 'null'):
                                param_value = float(pa.split(': ')[1])
                            tmp = pd.DataFrame([param_value], columns=[param_name])
                            t1 = pd.concat([t1, tmp], axis=1)
                        t2 = pd.concat([t2, t1], axis=1)
                        all_configs = pd.concat([all_configs, t2], ignore_index=True)
            f2.close()    

        return all_configs, exp_names, elite_ids

    def else_configs(self):
        """
        Read the at least top 5 configurations from the provided Crace results
        """

        # parameters need to be returned
        all_configs = pd.DataFrame()
        exp_names = []
        elite_ids = {}

        for folder in self.folders:
            name = os.path.basename(folder)
            exp_names.append(name)
            elite_ids[name] = []
            config_ids = []
            i = 0
            # read elite_log file to get the elitist configuration id
            with open(os.path.join(folder, self.elite_log)) as f1:
                for line in f1:
                    if i > 0 and i <= self.num_config:
                        elite_id = int(line.split(',')[-2])
                        elite_ids[name].append(elite_id)
                    i += 1
            f1.close()

            # firstly read the elite configurations
            tmp = t1 = t2 = pd.DataFrame()
            i = 0
            # read config_log file to get the details of each elitist configuration 
            with open(os.path.join(folder, self.config_log), 'r') as f2:
                for line in f2:
                    config_id = int(line.split(',')[0])
                    if config_id not in config_ids and i < len(elite_ids[name]) and config_id in elite_ids[name]:
                        i += 1
                        config_ids.append(config_id)
                        params = re.sub('"','',line.split('{')[1].split('}')[0])
                        t1 = pd.DataFrame([config_id], columns=['config_id'])
                        t2 = pd.DataFrame([name], columns=['exp_name'])
                        for pa in params.split(', '):
                            param_name = pa.split(': ')[0]
                            param_value = pa.split(': ')[1]
                            if 'i' in self.parameters[param_name]['type'] and param_value not in (None, 'null'):
                                param_value = int(pa.split(': ')[1])
                            elif 'r' in self.parameters[param_name]['type'] and param_value not in (None, 'null'):
                                param_value = float(pa.split(': ')[1])
                            tmp = pd.DataFrame([param_value], columns=[param_name])
                            t1 = pd.concat([t1, tmp], axis=1)
                        t2 = pd.concat([t2, t1], axis=1)
                        all_configs = pd.concat([all_configs, t2], ignore_index=True)
            f2.close()

            # secondly read the other configurations not in the elites list
            with open(os.path.join(folder, self.config_log), 'r') as f3:
                lines = f3.readlines()
                n = -1
                while i < self.num_config:
                    line = lines[n]
                    config_id = int(line.split(',')[0])
                    if config_id not in config_ids:
                        i += 1
                        config_ids.append(config_id)
                        params = re.sub('"','',line.split('{')[1].split('}')[0])
                        t1 = pd.DataFrame([config_id], columns=['config_id'])
                        t2 = pd.DataFrame([name], columns=['exp_name'])
                        for pa in params.split(', '):
                            param_name = pa.split(': ')[0]
                            param_value = pa.split(': ')[1]
                            if 'i' in self.parameters[param_name]['type'] and param_value not in (None, 'null'):
                                param_value = int(pa.split(': ')[1])
                            elif 'r' in self.parameters[param_name]['type'] and param_value not in (None, 'null'):
                                param_value = float(pa.split(': ')[1])
                            tmp = pd.DataFrame([param_value], columns=[param_name])
                            t1 = pd.concat([t1, tmp], axis=1)
                        t2 = pd.concat([t2, t1], axis=1)
                        all_configs = pd.concat([all_configs, t2], ignore_index=True)
                    n -= 1
            f3.close()

        return all_configs, exp_names, elite_ids

    def elites_process(self):
        """
        Read the quality of the final elite configurations sampled at the the process
        """

        all_configs = pd.DataFrame()
        exp_names = None

        folder = self.folders[0]
        name = os.path.basename(folder)
        dirname = os.path.basename(os.path.dirname(folder))
        exp_names = dirname + '/' + name
        elite_ids = []
        i = 0
        with open(os.path.join(folder, self.elite_log), "r") as f1:
            for line in f1:
                if i > 0 and i <= self.num_config:
                    elite_id = int(line.split(',')[-2])
                    elite_ids.append(elite_id)
                i += 1
        f1.close()
        
        tmp = pd.DataFrame()
        print("#   exps file:", os.path.join(folder, self.exps_fin))
        # read config_log file to get the details of each elitist configuration 
        with open(os.path.join(folder, self.exps_fin), 'r') as f2:
            for line in f2:
                line_result = json.loads(line)
                current_id = str(line_result["configuration_id"])
                if int(current_id) in elite_ids:
                    current_ins = str(line_result["instance_id"])
                    current_quality = line_result["quality"]
                    tmp = pd.DataFrame([[name, current_id, current_ins, current_quality]], \
                                        columns=['exp_name', 'config_id', 'instance_id', 'quality'])
                    all_configs = pd.concat([all_configs, tmp], ignore_index=True)
        f2.close()    
        return all_configs, exp_names, elite_ids

    def all_elite_process(self):
        """
        Read the quality of all elitist configurations sampled during the process
        """

        # parameters need to be returned
        all_configs = pd.DataFrame()
        exp_names = None
        elite_ids = []

        folder = self.folders[0]
        name = os.path.basename(folder)
        dirname = os.path.basename(os.path.dirname(folder))
        exp_names = dirname + '/' + name
        # read elites.log file to get the elitist configuration id
        with open(os.path.join(folder, self.all_elites), "r") as f1:
            for line in f1:
                elite_ids.append(int(re.sub("\D", "", line)))
        f1.close()
        elitist_id = elite_ids.pop()

        tmp = pd.DataFrame()
        print("#   exps file:", os.path.join(folder, self.exps_fin))
        # read config_log file to get the details of each elitist configuration 
        with open(os.path.join(folder, self.exps_fin), 'r') as f2:
            for line in f2:
                line_result = json.loads(line)
                current_id = str(line_result["configuration_id"])
                if int(current_id) in elite_ids:
                    current_ins = str(line_result["instance_id"])
                    current_quality = line_result["quality"]
                    # if int(current_id) == elitist_id:
                    #     current_id = "*%(num)s*" % {"num": elitist_id}
                    tmp = pd.DataFrame([[name, current_id, current_ins, current_quality]], \
                                        columns=['exp_name', 'config_id', 'instance_id', 'quality'])
                    all_configs = pd.concat([all_configs, tmp], ignore_index=True)
        f2.close() 

        elite_ids[elite_ids.index(elitist_id)] = "*%(num)s*" % {"num": elitist_id}

        return all_configs, exp_names, elite_ids

    def parse_parameters(self):
        """
        load the range of each parameter in the provided Crace results
        """
        
        # load the information from the provided Crace results
        # Only once
        flag = True
        for folder in self.folders:
            if flag is not True:
                break
            else:
                flag = False
                with open(os.path.join(folder, self.params), "r") as f:
                    line = json.loads(f.read())
                    tmp_params = line[0]
                f.close()
        
        # parse all parameters
        all_parameters = {}
        tmp_params = json.loads(json.dumps(tmp_params))
        for p in tmp_params:
            all_parameters[p['name']] = {}
            all_parameters[p['name']]['type'] = p['type']
            all_parameters[p['name']]['domain'] = p['domain']

        return(all_parameters)
