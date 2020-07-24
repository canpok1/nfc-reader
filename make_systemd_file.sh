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
StandardOutput = file:/var/log/nfc-reader.log
StandardError = file:/var/log/nfc-reader.log
User = pi
Group = pi

[Install]
WantedBy = multi-user.target
EOS

cat << EOS > /etc/systemd/system/nfc-reader-sender.service
[Unit]
Description = nfc reader sender

[Service]
ExecStart = ${dir}/start_nfc_reader_sender.sh
Type = oneshot
StandardOutput = file:/var/log/nfc-reader-sender.log
StandardError = file:/var/log/nfc-reader-sender.log
User = pi
Group = pi
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

