#!/bin/bash

apt install -y docker.io jq

# Create ubuntu user
useradd -m -s /bin/bash ubuntu

# Add ubuntu to groups
usermod -a -G docker,adm,sudo ubuntu

# Install software
cd /home/ubuntu
git clone https://github.com/bjucps/open-contest
cd open-contest
docker build -t bjucps/open-contest opencontest
cd runners
bash build.sh
cd /home/ubuntu
cp -r open-contest/test/db .

# Copy .ssh authorized keys to ubuntu user
cp -r ~/.ssh /home/ubuntu
chown -R ubuntu:ubuntu * .ssh

# Register system services
cp open-contest/*.service /etc/systemd/system
cd /etc/systemd/system
systemctl enable opencontest

