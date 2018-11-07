#!/bin/bash

# This script will query libvirt to get some information useful for
# debugging

# Environment variables:
# $LOG_DIR is the directory to copy logs to.
# $CONFIG_DIR is the directory to copy configuration from.

set +o errexit

copy_logs() {
    if ! command -v virsh > /dev/null 2>&1; then
        return 0
    fi

    virsh list --all > ${LOG_DIR}/libvirt_logs/list.txt
    virsh list --all --name | while read vm; do
        if [ "$vm" != "" ]; then
            virsh dumpxml "$vm" > ${LOG_DIR}/libvirt_logs/"$vm".txt
        fi
    done

}

copy_logs
