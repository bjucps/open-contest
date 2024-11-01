FROM eclipse-temurin:23-noble
RUN apt-get update 
RUN apt-get install -y python3

COPY java/main.py /main.py
COPY runner.py /runner.py
ENTRYPOINT ["python3", "main.py"]
