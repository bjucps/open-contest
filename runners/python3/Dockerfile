FROM python:3.12-bookworm
RUN apt-get update 

COPY python3/main.py /main.py
COPY runner.py /runner.py
ENTRYPOINT ["python3", "main.py"]
