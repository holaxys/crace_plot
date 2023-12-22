#!/bin/bash

set -e
set -o pipefail

# combine all parameters to $1
error () {
    echo "$0: error: $@" >&2
    exit 1
}

# Issue usage if no parameters are given.
if [ $# == 0 ]; then
	echo "Function: elites of an experiment on a group of instances"
    echo "Usage: ./sbatch.sh <EXPDIR> <INSFILE> "
    exit 1
fi

EXPDIR=$1
INSFILE=$2

EXECDIR=/home/ysxiao/race/dev_crace/plot-crace/util/elites_analysis

JOBNAME=elite
MACHINE=Epyc7452
# MACHINE=Xeon6138

CUR_TIME=$(date "+%m%d%H%M")

function submit(){
	exec sbatch <<EOF
#!/bin/sh
#SBATCH -J $JOBNAME
#SBATCH -p $MACHINE
#SBATCH -q long
#SBATCH -N 1 
#SBATCH --cpus-per-task=1
#SBATCH -o $EXPDIR/econfig_test_$CUR_TIME.stdout
#SBATCH -e $EXPDIR/econfig_test_$CUR_TIME.stderr

echo "$EXECDIR/elites_on_instances $EXPDIR $INSFILE"
$EXECDIR/elites_on_instances $EXPDIR $INSFILE

EOF
}

submit
