FROM mono:latest

RUN apt-get update && apt-get install -y python3
COPY cs/main.py /main.py
COPY runner.py /runner.py
ENTRYPOINT ["python3", "main.py"]
