import sys
import runner

runner.runCode(
    int(sys.argv[1]),
    int(sys.argv[2]),
    "javac code.java",
    "java code"
)