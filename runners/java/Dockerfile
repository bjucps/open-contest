FROM python:3.8-buster
RUN apt-get update 
RUN apt-get install -y openjdk-11-jdk

COPY java/main.py /main.py
COPY runner.py /runner.py
ENTRYPOINT ["python3", "main.py"]
