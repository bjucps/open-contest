FROM mcr.microsoft.com/dotnet/sdk:10.0

RUN apt-get update && apt-get install -y python3 

# Note: The following creates a new console project in a folder named app
# Then creates a soft link from the project's Program.cs file to the 
# /source/code.cs file where the contestant's source is located at container runtime

RUN dotnet new console -n app -o app \
    && mkdir /source \
    && mv /app/Program.cs /source/code.cs \
    && ln -s /source/code.cs /app/Program.cs
COPY cs/main.py /main.py
COPY runner.py /runner.py
ENTRYPOINT ["python3", "main.py"]
