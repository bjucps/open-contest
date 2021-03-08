import os

# return that amount of time the child process spent in user mode
def total_child_execution_time():
    f = open(f"/proc/{os.getpid()}/stat")
    data = f.read().split(" ")
    f.close()

    # return (cutime + cstime) / 100
    return (float(data[15]) + float(data[16])) / 100

def runCode(testCases: int, timeLimit: int, compile: str, run: str) -> int:

    os.chdir("/source")

    # print("Compiling...")

    # os.system("echo /source/out: $(ls /source)")
    
    # Compile submission
    if os.system(f"{compile} > out/compile_out.txt 2> out/compile_error.txt") != 0:
        print("compile_error")
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
            return 1
        
        # Check exit status of submission
        with open("out/result{0}.txt".format(i), "w") as f:
            f.write("ok" if status == 0 else "runtime_error")
    
    print("ok")
    return 0