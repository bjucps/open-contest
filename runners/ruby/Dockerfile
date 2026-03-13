FROM python:3.14
RUN apt-get update && apt-get install -y ruby

COPY ruby/main.py /main.py
COPY runner.py /runner.py
ENTRYPOINT ["python3", "main.py"]
