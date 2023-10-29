import sys
import runner

runner.runCode(
    int(sys.argv[1]),
    int(sys.argv[2]),
    "python3 -m py_compile code.py",
    "python3 code.py"
)