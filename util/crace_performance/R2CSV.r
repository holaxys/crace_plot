library("fs")
library(tibble)
require(stringr)

convert <- function(output){
  setwd(fs::path_norm(fs::path(output, "..")))
  load(output)
  id <- as.integer(colnames(iraceResults$testing$experiments)[1])
  best_id_info <- data.frame(best_id = integer(), stringsAsFactors=FALSE)
  best_id_info <- rbind(best_id_info, data.frame(best_id=id))
  write.table(best_id_info,"race_irace.log",row.names = FALSE, col.names = TRUE, sep = ",")
  
  test_results <- iraceResults$testing$experiments
  exps <- data.frame(experiment_id = integer(), quality = double(), stringsAsFactors=FALSE)
  for (i in 1:length(test_results)) {
    exps <- rbind(exps, data.frame(experiment_id=i, configuration_id=id, quality=test_results[i]))
  }
  write.table(exps,"exps_irace.log",row.names = FALSE, col.names = TRUE, sep = ",")
}

# setwd("/Users/xys/Library/CloudStorage/OneDrive-Personal/01_PhD/01_irace/Experiments/irace-r/")
dirs <- "/home/ysxiao/race/experiments/irace-r/acotspqap/tsp/irace_ttest"
dir_names <- list.dirs(dirs, full.names = TRUE, recursive = TRUE)

out_parrent_names <- list()
for (i in 1:length(dir_names)) {
  if (str_detect(dir_names[i], "exp")){
    # out_parrent_names <- append(out_parrent_names, dir_names[i], after = length(out_parrent_names))
    file_name <- paste(dir_names[i], "/irace.Rdata", sep = "", collapse = NULL)
    if (fs::is_file(file_name)){
      convert(file_name)
    }
  }
}


