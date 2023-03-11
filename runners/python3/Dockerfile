FROM python:3.10-buster
RUN apt-get update 

COPY python3/main.py /main.py
COPY runner.py /runner.py
ENTRYPOINT ["python3", "main.py"]
