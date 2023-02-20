import json
import os
import pandas as pd

class ReadResults:
    def __init__(self, folders):
        """
        Read Crace results from execDir

        :param num_repetitions: the number of repetitions of Crace in the given directory
        :param exec_dir: the directory stored Crace results
        """
        self.folders = folders

    def elite_configs_training(self):
        """
        Read Crace training results of the top5 elite configurations
        """
        
        exps_fin = "irace_log/exps_fin.log"
        elite_log = "irace_log/elite.log"
        # all_results = {}
        all_data = pd.DataFrame()
        exp_names = []
        elite_ids = {}

        for folder in self.folders:
            name = os.path.basename(folder)
            exp_names.append(name)
            elite_ids[name] = []
            i = 0
            with open(os.path.join(folder, elite_log), "r") as f1:
                for line in f1:
                    if i > 0 and i <= 5 :
                        elite_id = line.split(',')[-2]
                        elite_ids[name].append(elite_id)
                        # all_results[key] = []
                    i += 1
            f1.close()
            tmp = {}
            with open(os.path.join(folder, exps_fin), "r") as f2:
                for line in f2:
                    line_results = json.loads(line)
                    current_id = str(line_results["configuration_id"])
                    current_quality = line_results["quality"]
                    # print(current_id)
                    if current_id in elite_ids[name]:
                        tmp = {'exp_name': name, 'config_id': current_id, 'quality': current_quality}
                        all_data = all_data.append(tmp, ignore_index=True)
            f2.close

        return all_data, exp_names, elite_ids
        
    def elite_configs_test(self):
        """
        Read Crace test results of the top5 elite configurations
        """
        
        exps_fin = "irace_log/test/exps_fin.log"
        elite_log = "irace_log/elite.log"
        all_data = pd.DataFrame()
        exp_names = []
        elite_ids = {}

        for folder in self.folders:
            name = os.path.basename(folder)
            exp_names.append(name)
            elite_ids[name] = []
            i = 0
            with open(os.path.join(folder, elite_log), "r") as f1:
                for line in f1:
                    if i >0 and i <= 5:
                        elite_id = line.split(',')[-2]
                        elite_ids[name].append(elite_id)
                        # all_results[key] = []
                    i += 1
            f1.close()
            tmp = {}
            with open(os.path.join(folder, exps_fin), "r") as f2:
                for line in f2:
                    line_results = json.loads(line)
                    current_id = str(line_results["configuration_id"])
                    current_quality = line_results["quality"]
                    # print(current_id)
                    if current_id in elite_ids[name]:
                        tmp = {'exp_name': name, 'config_id': current_id, 'quality': current_quality}
                        all_data = all_data.append(tmp, ignore_index=True)
            f2.close

        return all_data, exp_names, elite_ids
        
    def elitist_test(self):
        pass

    def elitist_training(self):
        pass

    def all_configs_training(self):
        pass
