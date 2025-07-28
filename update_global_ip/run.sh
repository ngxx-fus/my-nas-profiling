#!/bin/bash

# Activate python-venv

echo "$(date '+%Y-%m-%d %H:%M:%S,%3N') - INFO - Python: $(which python)"

try=1000

internet_check(){
    if ping -c 4 8.8.8.8 > /dev/null; then
        return 0;
    else
        return -1;
    fi
}

while [ $try -gt 0 ]; do
    echo "--------------- Attempt <$try> ---------------"
    try=$(( $try-1 ))
    # Check internet connection
    internet_check
    if [ $? -eq 0 ];then 
        echo "$(date '+%Y-%m-%d %H:%M:%S,%3N') - INFO - Connected to Internet!"
        echo "$(date '+%Y-%m-%d %H:%M:%S,%3N') - INFO - Run Python-App..."
        /home/fus/miniforge3/envs/py3.8/bin/python update_global_ip.py
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S,%3N') - INFO - Unable to connect to Internet!"
        echo "$(date '+%Y-%m-%d %H:%M:%S,%3N') - INFO - Sleep for 5m before try again!"
        while true; do
            internet_check
            if [ $? -eq 0 ]; then
                break
            else
                sleep 15
            fi
        done   
    fi
done
