#!/bin/bash
export USER=nathantheinventor
export OC_PROJECT_NAME=open-contest

# Build Docker images
docker build c/       -t $USER/$OC_PROJECT_NAME-c-runner
docker build cpp/     -t $USER/$OC_PROJECT_NAME-cpp-runner
docker build cs/      -t $USER/$OC_PROJECT_NAME-cs-runner
docker build java/    -t $USER/$OC_PROJECT_NAME-java-runner
docker build python2/ -t $USER/$OC_PROJECT_NAME-python2-runner
docker build python3/ -t $USER/$OC_PROJECT_NAME-python3-runner
docker build ruby/    -t $USER/$OC_PROJECT_NAME-ruby-runner
docker build vb/      -t $USER/$OC_PROJECT_NAME-vb-runner

# Push Docker images to DockerHub
docker push $USER/$OC_PROJECT_NAME-c-runner
docker push $USER/$OC_PROJECT_NAME-cpp-runner
docker push $USER/$OC_PROJECT_NAME-cs-runner
docker push $USER/$OC_PROJECT_NAME-java-runner
docker push $USER/$OC_PROJECT_NAME-python2-runner
docker push $USER/$OC_PROJECT_NAME-python3-runner
docker push $USER/$OC_PROJECT_NAME-ruby-runner
docker push $USER/$OC_PROJECT_NAME-vb-runner
