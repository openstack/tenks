#!/bin/bash

# NOTE(wszumski): This has been adapted from tests/get_logs.sh in Kayobe.

# Environment variables:
# $LOG_DIR is the directory to copy logs to.
# $CONFIG_DIR is the directory to copy configuration from.

set +o errexit

copy_logs() {
    if [[ -d ${CONFIG_DIR} ]]; then
        cp -rnL ${CONFIG_DIR}/* ${LOG_DIR}/config/
    fi
    cp -rvnL /var/log/* ${LOG_DIR}/system_logs/

    if [[ -x "$(command -v journalctl)" ]]; then
        journalctl --no-pager > ${LOG_DIR}/system_logs/syslog.txt
    fi

    cp -r /etc/sudoers.d ${LOG_DIR}/system_logs/
    cp /etc/sudoers ${LOG_DIR}/system_logs/sudoers.txt

    df -h > ${LOG_DIR}/system_logs/df.txt
    free  > ${LOG_DIR}/system_logs/free.txt
    parted -l > ${LOG_DIR}/system_logs/parted-l.txt
    mount > ${LOG_DIR}/system_logs/mount.txt
    env > ${LOG_DIR}/system_logs/env.txt
    ip address > ${LOG_DIR}/system_logs/ip-address.txt
    ip route > ${LOG_DIR}/system_logs/ip-route.txt

    iptables-save > ${LOG_DIR}/system_logs/iptables.txt

    if [ `command -v dpkg` ]; then
        dpkg -l > ${LOG_DIR}/system_logs/dpkg-l.txt
    fi
    if [ `command -v rpm` ]; then
        rpm -qa > ${LOG_DIR}/system_logs/rpm-qa.txt
    fi

    # final memory usage and process list
    ps -eo user,pid,ppid,lwp,%cpu,%mem,size,rss,cmd > ${LOG_DIR}/system_logs/ps.txt

    # Rename files to .txt; this is so that when displayed via
    # logs.openstack.org clicking results in the browser shows the
    # files, rather than trying to send it to another app or make you
    # download it, etc.
    for f in $(find ${LOG_DIR}/{system_logs,libvirt_logs} -name "*.log"); do
        mv $f ${f/.log/.txt}
    done

    chmod -R 777 ${LOG_DIR}
    find ${LOG_DIR}/{system_logs,libvirt_logs} -iname '*.txt' -execdir gzip -f -9 {} \+
    find ${LOG_DIR}/{system_logs,libvirt_logs} -iname '*.json' -execdir gzip -f -9 {} \+
}

copy_logs
