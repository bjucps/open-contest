import sys
import runner

runner.runCode(
    int(sys.argv[1]),
    int(sys.argv[2]),
    "g++ -std=c++17 -O2 code.cpp -o code",
    "./code"
)