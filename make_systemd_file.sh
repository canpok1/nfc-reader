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
StandardOutput = append:/var/log/nfc-reader.log
StandardError = append:/var/log/nfc-reader.log

[Install]
WantedBy = multi-user.target
EOS

cat << EOS > /etc/systemd/system/nfc-reader-sender.service
[Unit]
Description = nfc reader sender

[Service]
ExecStart = ${dir}/start_nfc_reader_sender.sh
Type = oneshot
User = pi
Group = pi
StandardOutput = append:/var/log/nfc-reader-sender.log
StandardError = append:/var/log/nfc-reader-sender.log
EOS

cat << EOS > /etc/systemd/system/nfc-reader-sender.timer
[Unit]
Description = schedule nfc reader sender

[Timer]
Unit=nfc-reader-sender.service
OnCalendar=*:0/3

[Install]
WantedBy=timers.target
EOS

