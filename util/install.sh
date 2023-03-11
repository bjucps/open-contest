#!/bin/bash

USER=cms

apt install -y docker.io jq

# Create user
useradd -m -s /bin/bash $USER

# Add $USER to groups
usermod -a -G docker,adm,sudo $USER

# Install software
cd /home/$USER
git clone https://github.com/bjucps/open-contest
cd open-contest
docker build -t bjucps/open-contest opencontest
cd runners
bash build.sh
cd /home/$USER
cp -r open-contest/test/db .

# Copy .ssh authorized keys to $USER user
cp -r ~/.ssh /home/$USER
chown -R $USER:$USER * .ssh

# Register system services
cp open-contest/*.service /etc/systemd/system
cd /etc/systemd/system
systemctl enable opencontest

