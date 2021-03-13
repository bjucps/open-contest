# OpenContest

OpenContest is an open-source programming contest management system written in
Python, using Docker technology. It allows judges to write problems and contest
participants to submit solutions to those problems. 

## Features

* OpenContest tests contestant submissions automatically, using one or more data
  sets. If a submission is correct, or has a compile error, or exceeds the
  allowed time limits, the contestant is automatically notified of the result
  with no judge intervention. If the submission has incorrect output, the submission
  is placed into a judging queue for manual review by judges to determine an appropriate
  response. 
  
* When checking the output, the system ignores whitespace at the ends of lines and at the
  end of the output.

* The system allows per-problem time limits to be specified. Also, a system-wide maximum
  allowed output length limit is configurable.

* Multiple judges may participate in reviewing contestant submissions. The system
  handles scenarios where multiple judges attempt to check out the same submission from the
  submission queue for judging.

## Quick Start for Ubuntu 18.04

Execute the following to install Docker:
```
sudo apt install docker.io
```

Execute the following to add the current user to the docker group
so that docker commands can be executed without using sudo:
```
sudo usermod -a -G docker $USER
```

Logout, then login to make the change take effect. Then, install the open-contest docker image:

```
$> docker pull bjucps/open-contest
Using default tag: latest
latest: Pulling from bjucps/open-contest
Digest: sha256:9f65996f196f8780956cd08b9ed53d84f4e26c5e8456fe50c6487e8a5f316948
Status: Image is up to date for bjucps/open-contest:latest
```

Finally, download the launch script and use it to start the contest server:

```
$> wget https://raw.githubusercontent.com/bjucps/open-contest/master/launch.sh
$> wget https://raw.githubusercontent.com/bjucps/open-contest/master/open-contest.config
$> bash launch.sh
```

The launch script will create a folder for the contest database in your home directory named
**db** and start the open contest server. Open the db/open-contest.log file to view the 
Admin username and password to use to login. Navigate to [localhost](http://localhost),
enter `Admin` as the username and enter the password generated by OpenContest.

If desired, copy open-contest.config from the github project into the db folder and edit
configuration settings there.

Use the web interface to create problems, a contest to hold them, and users to participate

## How it works

OpenContest runs inside a Docker container and starts other containers on the host machine to run submissions. 


## Documentation

* [User Manual](MANUAL.md)
* [Development Guide](README-devsetup.md).]
