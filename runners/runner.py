import os

# Return amount of CPU time the child process
# spent in user mode and system mode in seconds
def total_child_execution_time():
    with open(f"/proc/{os.getpid()}/stat") as f:
        data = f.read().split(" ")

    # See https://man7.org/linux/man-pages/man5/procfs.5.html for more details
    cutime = float(data[15]) # total child process CPU time in user mode
    cstime = float(data[16]) # total child process CPU time in kernel mode
    return (cutime + cstime) / 100

def runCode(testCases: int, timeLimit: int, compile: str, run: str, switchStdOutErr = False) -> int:

    os.chdir("/source")
    
    stdout = "out/compile_out.txt"
    stderr = "out/compile_error.txt"

    # Some languages, like C# and VB, print compile errors
    # to stderr instead of stdout
    if switchStdOutErr:
        temp = stdout
        stdout = stderr
        stderr = stdout

    # Compile submission
    if os.system(f"{compile} > {stdout} 2> {stderr}") != 0:
        print("compile_error")
        os.chdir("..")
        return 1
    
    # Get the child CPU time after compile is done so that 
    # we can measure the CPU time spent running test cases 
    start_time = total_child_execution_time()
    
    # Run test cases
    for i in range(testCases):
        status = os.system("ulimit -t {0} ; {1} < in{2}.txt > out/out{2}.txt 2> out/err{2}.txt".format(timeLimit + 1, run, i))
        
        # Get the current CPU time of submission and report TLE
        # if time is over
        currentTime = total_child_execution_time() - start_time
        if currentTime > timeLimit:
            print("TLE")
            os.chdir("..")
            return 1
        
        # Check exit status of submission
        with open(f"out/result{i}.txt", "w") as f:
            f.write("ok" if status == 0 else "runtime_error")
    
    print("ok")
    os.chdir("..")

    return 0