import sys
import runner

runner.runCode(
    int(sys.argv[1]),
    int(sys.argv[2]),
    "gcc -std=c11 -O2 code.c -o code",
    "./code"
)