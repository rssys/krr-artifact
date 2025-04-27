#!/bin/bash

basedir=${1}
test=${2}
schemes_arg=${3:-"baseline,kernel_rr,whole_system_rr"}

CUR_DIR=$(pwd)
QEMU_DIR="qemu-tcg-kvm"
RES_DIR="$test-data"
GRAPH_SCRIPT="draw_kernelcompile_graph.py"

mkdir -p ${RES_DIR}
rm -f ${RES_DIR}/*
rm -f ${QEMU_DIR}/kernel_rr/test_data/*
echo "Cleaned data in ${QEMU_DIR}/kernel_rr/test_data ${RES_DIR}"

cd ${QEMU_DIR}/kernel_rr

# Convert comma-separated schemes argument to an array
IFS=',' read -r -a schemes <<< "$schemes_arg"

echo "Testing on $schemes_arg"

# Loop through the array
for scheme in "${schemes[@]}"
do
    # Set the branch variable based on the scheme
    case $scheme in
        "baseline")
            branch="native"
            ;;
        "kernel_rr")
            branch="rr-para"
            ;;
        "whole_system_rr")
            branch="all-rr"
            ;;
        *)
            echo "Unknown scheme: $scheme"
            continue
            ;;
    esac

    # Output the current scheme and its corresponding branch
    echo "Scheme: $scheme, Branch: $branch"
    cd ${basedir}/kernel-rr-linux/;git checkout $branch;sh replace.sh

    cd ${basedir}/qemu-tcg-kvm/kernel_rr/;bash observer_script.sh $scheme $test $test $basedir
    if [ -f "/dev/shm/quit" ]; then
            echo "Ending test..."
            exit 0
    fi
done

cd ${CUR_DIR}
mv ${QEMU_DIR}/kernel_rr/test_data/*.csv $RES_DIR/
echo "Results are under $RES_DIR/"
cd graph/; python3 ${GRAPH_SCRIPT}
