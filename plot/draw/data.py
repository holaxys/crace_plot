import json
import os
import re
import pandas as pd

from plot.containers.read_options import ReadOptions

class ReadResults:
    def __init__(self, folders, options: ReadOptions):
        """
        Read Crace results from execDir

        :param num_repetitions: the number of repetitions of Crace in the given directory
        :param exec_dir: the directory stored Crace results
        """
        self.folders = folders

        self.elite_log = ""
        self.exps_fin = ""

        if options.numConfigurations.value == "elites":
            self.num_config = 5
        elif options.numConfigurations.value == "elitist":
            self.num_config = 1
        else:
            self.num_config = -1

        self.config_type = options.configType.value

        # select exact way to load Crace results via :param{drawMethod}
        # e.g.: heatmap for config_data; boxplot for performance
        self.draw_method = options.drawMethod.value

    def load_for_perfomance(self):
        """
        Read elite configurations (the best or the top 5 ) in Crace training results
        Tips: the quality of each experiments on different configurations
        """

        self.elite_log = "irace_log/elite.log"
        self.exps_fin = "irace_log/exps_fin.log" if self.config_type == "training" else "irace_log/test/exps_fin.log"

        all_data, exp_names, elite_ids = self.elites_quality() if self.num_config == 5 else self.elitist_quality()

        return all_data, exp_names, elite_ids
    
    def load_for_configs_data(self):
        """
        Read configurations (the best or the top 5 ) in Crace results
        Tips: the value of parameters for each configuration
        """
        
        self.elite_log = "irace_log/elite.log"
        self.config_log = "irace_log/config.log"
        self.params = "irace_log/parameters.log"

        parameters = self.parse_parameters()

        if self.num_config != -1:
            all_configs, config_ids, elite_ids = self.elite_configs() if self.num_config == 5 else self.elitist_config()
        
        return all_configs, config_ids, elite_ids, parameters

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
                        elite_id = line.split(',')[-2]
                        elite_ids[name].append(elite_id)
                    i += 1
            f1.close()
            tmp = {}
            with open(os.path.join(folder, self.exps_fin), "r") as f2:
                for line in f2:
                    line_results = json.loads(line)
                    current_id = str(line_results["configuration_id"])
                    current_quality = line_results["quality"]
                    if current_id in elite_ids[name]:
                        tmp = {'exp_name': name, 'config_id': current_id, 'quality': current_quality}
                        all_data = all_data.append(tmp, ignore_index=True)
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
                        elite_id = line.split(',')[-2]
                        elitist_ids['elitist'].append(elite_id)
                        elite_ids[name].append(elite_id)
                    i += 1
            f1.close()
            tmp = {}
            with open(os.path.join(folder, self.exps_fin), "r") as f2:
                for line in f2:
                    line_results = json.loads(line)
                    current_id = str(line_results["configuration_id"])
                    current_quality = line_results["quality"]
                    if current_id in elite_ids[name]:
                        tmp = {'exp_name': name, 'config_id': current_id, 'quality': current_quality}
                        all_data = all_data.append(tmp, ignore_index=True)
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
                        elite_id = line.split(',')[-2]
                        elite_ids[name].append(elite_id)
                    i += 1
            f1.close()

            t1 = t2 = {}
            # read config_log file to get the details of each elitist configuration 
            with open(os.path.join(folder, self.config_log), 'r') as f2:
                for line in f2:
                    config_id = line.split(',')[0]
                    if config_id not in config_ids and config_id in elite_ids[name]:
                        config_ids.append(config_id)
                        params = re.sub('"','',line.split('{')[1].split('}')[0])
                        t1['config_id'] = config_id
                        for pa in params.split(', '):
                            t1[pa.split(': ')[0]] = pa.split(': ')[1]
                        t2 = {'exp_name': name, 'config_id': config_id}
                        t2.update(t1)
                        all_configs = all_configs.append(t2, ignore_index=True)
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
            i = 0
            # read elite_log file to get the elitist configuration id
            with open(os.path.join(folder, self.elite_log)) as f1:
                for line in f1:
                    if i == 1:
                        elite_id = line.split(',')[-2]
                        elite_ids[name].append(elite_id)
                        elitist_ids['elitist'].append(elite_id)
                    i += 1
            f1.close()

            # read config_log file to get the details of each elitist configuration 
            t1 = t2 = {}
            with open(os.path.join(folder, self.config_log), 'r') as f2:
                for line in f2:
                    config_id = line.split(',')[0]
                    if config_id in elite_ids[name]:
                        params = re.sub('"','',line.split('{')[1].split('}')[0])
                        t1['config_id'] = config_id
                        for pa in params.split(', '):
                            t1[pa.split(': ')[0]] = pa.split(': ')[1]
                        t2 = {'exp_name': name, 'config_id': config_id}
                        t2.update(t1)
                        all_configs = all_configs.append(t2, ignore_index=True)
            f2.close()  

        return all_configs, exp_names, elitist_ids

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
