import os
import logging
from code.util import register
from code.util.db import Submission, Problem
import time
import shutil

def addSubmission(probId, lang, code, user, type):
    sub = Submission()
    sub.problem = Problem.get(probId)
    sub.language = lang
    sub.code = code
    sub.result = "pending"
    sub.user = user
    sub.timestamp = time.time()
    sub.type = type
    sub.save()
    return sub

exts = {
    "c": "c",
    "cpp": "cpp",
    "cs": "cs",
    "java": "java",
    "python2": "py",
    "python3": "py",
    "ruby": "rb",
    "vb": "vb"
}

def readFile(path):
    try:
        with open(path, "rb") as f:
            return f.read().decode("utf-8")
    except:
        return None

def runCode(sub):
    # Copy the code over to the runner /tmp folder
    extension = exts[sub.language]
    os.mkdir(f"/tmp/{sub.id}")
    with open(f"/tmp/{sub.id}/code.{extension}", "wb") as f:
        f.write(sub.code.encode("utf-8"))
    
    prob = sub.problem
    tests = prob.samples if sub.type == "test" else prob.tests
    
    # Copy the input over to the tmp folder for the runner
    for i in range(tests):
        shutil.copyfile(f"/db/problems/{prob.id}/input/in{i}.txt", f"/tmp/{sub.id}/in{i}.txt")

    # Output files will go here
    os.mkdir(f"/tmp/{sub.id}/out")

    # Run the runner
    if os.system(f"docker run --network=none -m 256MB -v /tmp/{sub.id}/:/source nathantheinventor/open-contest-dev-{sub.language}-runner {tests} 5 > /tmp/{sub.id}/result.txt") != 0:
        raise Exception("Something went wrong")

    inputs = []
    outputs = []
    answers = []
    errors = []
    results = []
    result = "ok"

    for i in range(tests):
        inputs.append(sub.problem.testData[i].input)
        errors.append(readFile(f"/tmp/{sub.id}/out/err{i}.txt"))
        outputs.append(readFile(f"/tmp/{sub.id}/out/out{i}.txt"))
        answers.append(sub.problem.testData[i].output)
        
        res = readFile(f"/tmp/{sub.id}/out/result{i}.txt")
        if res == "ok" and answers[-1].strip() != outputs[-1].strip():
            res = "wrong_answer"
        if res == None:
            res = "tle"
        results.append(res)

        # Make result the first incorrect result
        if res != "ok" and result == "ok":
            result = res

    sub.result = result
    if readFile(f"/tmp/{sub.id}/result.txt") == "compile_error\n":
        sub.result = "compile_error"
        sub.delete()
        sub.compile = readFile(f"/tmp/{sub.id}/out/compile_error.txt")
        return

    sub.results = results
    sub.inputs = inputs
    sub.outputs = outputs
    sub.answers = answers
    sub.errors = errors

    sub.save()

    shutil.rmtree(f"/tmp/{sub.id}", ignore_errors=True)

def submit(params, setHeader, user):
    probId = params["problem"]
    lang   = params["language"]
    code   = params["code"]
    type   = params["type"]
    submission = addSubmission(probId, lang, code, user, type)
    runCode(submission)
    return submission.toJSON()

register.post("/submit", "loggedin", submit)