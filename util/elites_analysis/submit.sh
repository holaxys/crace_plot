#!/bin/sh

if [ $# -lt 1 ]; then
    echo -e " Usage: ./submit <DIR_OF_EXP> \n eg: ./submit path/to/acotsp "
    exit 1
fi

EXPDIR=$1
# instances list file
# INSFILE=/home/ysxiao/irace/instances/tsp/instances/list_200_train_16
# INSFILE=/home/ysxiao/irace/instances/tsp/instances/list_200_test_78
INSFILE="instances.log"

CURRENT_DIR=/home/ysxiao/race/dev_crace/plot-crace/util/elites_analysis

# only crace
###########################################################################################
# NUM=`find $EXPDIR -type f | grep "para" | grep "elites.log" | sort -n | wc -l`

# find $EXPDIR -type f | grep "para" | grep "elites.log" | sort -n | while read file_line
# do
# 	DIR_FILE=${file_line%/*}
# 	#echo $DIR_FILE >> $CURRENT_DIR/$JOBSLIST
# 	$CURRENT_DIR/sbatch.sh $DIR_FILE $INSFILE
# done
###########################################################################################

# only irace
###########################################################################################
# NUM=`find $EXPDIR -type f | grep "irace/exp-" | grep "elites.log" | sort -n | wc -l`

# find $EXPDIR -type f | grep "irace/exp-" | grep "elites.log" | sort -n | while read file_line
# do
# 	DIR_FILE=${file_line%/*}
# 	# echo $DIR_FILE
# 	$CURRENT_DIR/sbatch.sh $DIR_FILE $INSFILE
# done
###########################################################################################

# irace and crace
###########################################################################################
NUM=`find $EXPDIR -type f | grep "elites.log" | sort -n | wc -l`

find $EXPDIR -type f | grep "elites.log" | sort -n | while read file_line
do
	DIR_FILE=${file_line%/*}
	# echo $DIR_FILE
	echo "$CURRENT_DIR/sbatch.sh $DIR_FILE $INSFILE"
	$CURRENT_DIR/sbatch.sh $DIR_FILE $INSFILE
done
###########################################################################################