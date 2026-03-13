import sys
import runner

runner.runCode(
    int(sys.argv[1]),
    int(sys.argv[2]),
    # Build the project in the /app folder
    "dotnet build /app",
    # Run the project in the /app folder
    "dotnet run --project /app",
    True
)