import sys
import runner

runner.runCode(
    int(sys.argv[1]),
    int(sys.argv[2]),
    "ruby -c code.rb",
    "ruby code.rb"
)