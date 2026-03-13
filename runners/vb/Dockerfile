FROM mcr.microsoft.com/dotnet/sdk:10.0

RUN apt-get update && apt-get install -y python3

# Note: The following creates a new console project in a folder named app
# Then creates a soft link from the project's Program.cs file to the 
# /source/code.cs file where the contestant's source is located at container runtime

RUN dotnet new console --language VB -n app -o app \
    && mkdir /source \
    && mv /app/Program.vb /source/code.vb \
    && ln -s /source/code.vb /app/Program.vb
COPY vb/main.py /main.py
COPY runner.py /runner.py
ENTRYPOINT ["python3", "main.py"]
