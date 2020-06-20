#!/bin/bash
cd $(dirname $0)
dir=$(pwd)

cat << EOS > /etc/systemd/system/nfc-reader.service
[Unit]
Description = nfc reader

[Service]
ExecStart = ${dir}/start_nfc_reader.sh
Restart = always
Type = simple

[Install]
WantedBy = multi-user.target
EOS

