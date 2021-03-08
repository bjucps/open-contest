import sys
import runner

runner.runCode(
    int(sys.argv[1]),
    int(sys.argv[2]),
    "vbnc code.vb",
    "mono code.exe"
)