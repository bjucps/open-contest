#!/bin/bash

apt install -y docker.io
useradd -m -s /bin/bash ubuntu
usermod -a -G docker ubuntu

cd /home/ubuntu
git clone https://github.com/bjucps/open-contest
cd open-contest
docker build -t bjucps/open-contest opencontest
cd runners
bash build.sh
cd /home/ubuntu
cp -r open-contest/test/db .
chown -R ubuntu:ubuntu *

cp open-contest/*.service /etc/systemd/system
cd /etc/systemd/system
systemctl enable cloudflare
systemctl enable opencontest
