library("fs")
library(tibble)
require(stringr)

current <- getwd()
on.exit(setwd(current))

convert <- function(output){
  initial_dir <- getwd()
  on.exit(setwd(initial_dir), add = TRUE)

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

  allelites <- iraceResults$allElites
  ids <- unique(sapply(allelites, function(x) x[1]))
  elites <- data.frame(elite_id = integer(), stringsAsFactors=FALSE)
  elites <- rbind(elites, data.frame(elite_id=ids))
  final_info <- paste("Final best configuration: ", ids[length(ids)])
  elites <- rbind(elites, data.frame(elite_id=final_info))
  write.table(elites,"elites.log",row.names = FALSE, col.names = FALSE, quote = FALSE)

  params <- paste(iraceResults$parameters$names, collapse=",")
  params <- paste(params, ",.ID,.PARENT")
  elites_info <- data.frame(id = integer(), stringsAsFactors=FALSE)
  elites_info <- rbind(elites_info, data.frame(id=params))
  elites <- iraceResults$allElites[length(iraceResults$allElites)]
  cols <- names(iraceResults$allConfigurations)[-1]
  new_order <- c(cols[1:(length(cols)-1)], names(iraceResults$allConfigurations)[1], cols[length(cols)])
  new_allConf <- iraceResults$allConfigurations[, new_order]
  for (i in elites){
    for (x in i){
      info <- new_allConf[new_allConf$.ID. == x, ]
      info <- paste(info, collapse=",")
      elites_info <- rbind(elites_info, data.frame(id=info))
    }
  }
  write.table(elites_info,"race_log/elite.log",row.names = FALSE, col.names = FALSE, quote = FALSE)
}

dirs <- "/home/ysxiao/race/experiments/crace/crace2.0/time/mik/i322"
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

setwd(current)
