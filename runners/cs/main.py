import sys
import runner

runner.runCode(
    int(sys.argv[1]),
    int(sys.argv[2]),
    "csc code.cs -out:code.exe",
    "mono code.exe",
    True
)