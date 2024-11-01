import os
import logging
import time
import shutil
import re
import base64
import json
import io
import traceback
from threading import Thread

from uuid import uuid4
from zipfile import ZipFile

from django.http import JsonResponse

from contest.auth import logged_in_required, admin_required
from contest.models.problem import Problem
from contest.models.submission import Submission
from contest.models.contest import Contest
from contest.models.user import User
from contest.models.status import Status

from opencontest.settings import OC_MAX_DISPLAY_LEN, OC_MAX_OUTPUT_LEN, OC_DOCKERIMAGE_BASE

logger = logging.getLogger(__name__)

def addSubmission(probId, lang, code, user, type, custominput):
    sub = Submission()
    sub.problem = Problem.get(probId)
    sub.language = lang
    sub.code = code
    sub.result = Submission.RESULT_PENDING
    sub.custominput = custominput
    sub.user = user
    sub.timestamp = time.time() * 1000
    sub.type = type
    sub.status = Submission.STATUS_REVIEW
    
    if type == Submission.TYPE_SUBMIT:
        sub.save()
    else:
        sub.id = str(uuid4())

    return sub


exts = {
    "c": "c",
    "cpp": "cpp",
    "cs": "cs",
    "java": "java",
    "python3": "py",
    "ruby": "rb",
    "vb": "vb"
}


def readFile(path):
    """Reads file at `path` and returns string of at most OC_MAX_OUTPUT_LEN"""
    try:
        with open(path, "rb") as f:
            data = bytearray(f.read(OC_MAX_OUTPUT_LEN))

            for i, value in enumerate(data):
                if value == 10 or (value <= 127 and chr(value).isprintable()):
                    pass  
                elif value == 13:
                    data[i] = 32  # ignore carriage returns
                else:
                    data[i] = 63  # other characters map to ?

            result = data.decode('ascii')
            if f.read(1):
                result += "...\nadditional output not retained ..."
            return result
    except FileNotFoundError:
        return None
    except Exception:
        logger.exception('Error reading file ' + path)
        return None


def writeFile(path: str, data: str):
    with open(path, "w") as f:
        if data != None:
            f.write(data)


# Saves and truncates <data>
def saveData(sub: Submission, data: list, fileType: str):
    for i in range(len(data)):
        if sub.type == Submission.TYPE_SUBMIT:
            writeFile(f"/db/submissions/{sub.id}/{fileType}{i}.txt", data[i])
        data[i] = Submission.truncateForDisplay(data[i])


# Remove trailing whitespace
def strip(text):
    return re.sub("[ \t\r]*\n", "\n", text or "").rstrip()


# Checks if <incomplete> contains only lines from <full> in order
# Can be missing some lines in the middle or at the end
def compareStrings(incomplete: list, full: list) -> bool:
    lineNumOfFull = 0
    for line in incomplete:
        while lineNumOfFull < len(full):
            if line == full[lineNumOfFull]:
                break
            lineNumOfFull += 1
        else:
            return False
        lineNumOfFull += 1
    return True


def runCode(sub: Submission, user: User) -> list:
    """Executes submission `sub` and returns lists of data files"""
    extension = exts[sub.language]

    # Use semaphore to throttle number of concurrent submissions
    with Submission.runningSubmissions:
        try:
            shutil.rmtree(f"/tmp/{id}", ignore_errors=True)
            os.makedirs(f"/tmp/{sub.id}", exist_ok=True)

            # Copy the code over to the runner /tmp folder
            writeFile(f"/tmp/{sub.id}/code.{extension}", sub.code)
            
            prob = sub.problem
            
            if sub.type == Submission.TYPE_TEST and not user.isAdmin():
                numTests = prob.samples 
            elif sub.type == Submission.TYPE_CUSTOM:
                numTests = 1
            else:
                numTests = prob.tests     

            # Copy the input over to the tmp folder for the runner
            if sub.type == Submission.TYPE_CUSTOM:
                writeFile(f"/tmp/{sub.id}/in0.txt", sub.custominput)    
            else:
                for i in range(numTests):
                    with open(f"/db/problems/{prob.id}/input/in{i}.txt") as in_file:
                        data = in_file.read()
                    with open(f"/tmp/{sub.id}/in{i}.txt", "w") as out_file:
                        out_file.write(data.replace('\r', ''))

            # Output files will go here
            os.makedirs(f"/tmp/{sub.id}/out", exist_ok=True)

            # Run the runner
            cmd = f"docker run --rm --network=none -m 256MB -v /tmp/{sub.id}/:/source {OC_DOCKERIMAGE_BASE}-{sub.language}-runner {numTests} {prob.timelimit} > /tmp/{sub.id}/result.txt"
            logger.debug(cmd)
            rc = os.system(cmd)

            overall_result = readFile(f"/tmp/{sub.id}/result.txt")

            if rc != 0 or not overall_result:
                # Test failed to complete properly

                logger.warn(f"Result of submission {sub.id}: rc={rc}, overall_result={overall_result}")

                sub.result = "internal_error"
                if sub.type == Submission.TYPE_SUBMIT:
                    sub.save()
                return [], [], [], []

            logger.info("Overall result: '" + overall_result + "'")

            # Check for compile error
            if overall_result == "compile_error\n":
                logger.info("Compile error")
                sub.result = "compile_error"
                sub.delete()
                sub.compile = readFile(f"/tmp/{sub.id}/out/compile_error.txt")
                return None, None, None, None

            # Submission ran; process test results

            inputs = []
            outputs = []
            answers = []
            errors = []
            results = []
            result = "ok"

            all_samples_correct = True
            for i in range(numTests):
                if sub.type == Submission.TYPE_CUSTOM:
                    inputs.append(sub.custominput)
                    answers.append("")
                else:
                    inputs.append(sub.problem.testData[i].input)
                    answers.append(readFile(f"/db/problems/{prob.id}/output/out{i}.txt"))

                errors.append(readFile(f"/tmp/{sub.id}/out/err{i}.txt"))
                outputs.append(readFile(f"/tmp/{sub.id}/out/out{i}.txt"))

                anstrip = strip(answers[-1])
                outstrip = strip(outputs[-1])
                answerLines = anstrip.split('\n')
                outLines = outstrip.split('\n')

                res = readFile(f"/tmp/{sub.id}/out/result{i}.txt")
                if res == None:
                    res = "tle"
                elif res == "ok" and anstrip != outstrip:
                    if sub.type == Submission.TYPE_CUSTOM:
                        pass  # custom input cannot produce incorrect result
                    elif compareStrings(outLines, answerLines):
                        res = "incomplete_output"
                    elif compareStrings(answerLines, outLines):
                        res = "extra_output"
                    else:
                        res = "wrong_answer"
                
                results.append(res)

                # Make result the first incorrect result
                if res != "ok" and result == "ok":
                    result = res

                if i < prob.samples and res != "ok":
                    all_samples_correct = False

            may_autojudge = True
            if res == "wrong_answer" and sub.result == "presentation_error":
                # During a rejudge, do not replace "presentation_error" with "wrong_answer"
                pass
            else:
                sub.result = result

            if Contest.getCurrent():
                if Contest.getCurrent().tieBreaker and all_samples_correct and sub.result in ["runtime_error", "tle"]:
                    # Force review of submissions where all sample tests were correct if samples break ties
                    may_autojudge = False
                    
            if sub.result == "ok" or sub.type == Submission.TYPE_TEST or (may_autojudge and sub.result in ["runtime_error", "tle"]):
                sub.status = Submission.STATUS_JUDGED
                
            sub.results = results

            logger.debug(f"Result of testing {sub.id}: {sub}")

            saveData(sub, inputs, 'in')
            saveData(sub, outputs, 'out')
            saveData(sub, answers, 'answer')
            saveData(sub, errors, 'error')
            if sub.type == Submission.TYPE_SUBMIT:
                sub.save()

            return inputs, outputs, answers, errors

        finally:
            shutil.rmtree(f"/tmp/{sub.id}", ignore_errors=True)


# Process contestant test or submission
@logged_in_required
def submit(request, *args, **kwargs):
    user = User.getCurrent(request)
    probId = request.POST["problem"]
    lang = request.POST["language"]
    code = request.POST["code"]
    type = request.POST["type"]    # Submission.TYPE_*
    custominput = request.POST.get("input")
    submission = addSubmission(probId, lang, code, user, type, custominput)
    if submission.type == Submission.TYPE_TEST and not submission.problem.samples:
        return JsonResponse({"result": "internal_error", "error": 
            "Cannot run test because no sample test cases are defined for this problem. Make sure Number of Sample Cases for this problem is at least 1."})

    inputs, outputs, answers, errors = runCode(submission, user)
    response = submission.toJSON()
    if (submission.type == Submission.TYPE_SUBMIT or
       (submission.type == Submission.TYPE_TEST and user.isAdmin())):
        response["result"] = submission.getContestantResult()
        response["results"] = submission.getContestantIndividualResults()

    response["inputs"] = inputs
    response["outputs"] = outputs
    response["answers"] = answers
    response["errors"] = errors
    return JsonResponse(response)


@admin_required
def changeResult(request, *args, **kwargs):
    version = int(request.POST["version"])
    id = request.POST["id"]
    sub = Submission.get(id)
    if not sub:
        return JsonResponse("Error: no such submission", safe=False)
    
    if sub.changeResult(request.POST["result"], request.POST["status"], version):
        sub.save()
    else:
        return JsonResponse(
            "The submission has been changed by another judge since you loaded it. Please reload the sumbission to "
            "modify it.",
            safe=False
        )
    return JsonResponse("ok", safe=False)


@admin_required
def rejudge(request):
    """Ajax method: Rejudge a single submission `id`"""
    user = User.getCurrent(request)
    id = request.POST["id"]
    submission = Submission.get(id)
    runCode(submission, user)
    return JsonResponse(submission.result, safe=False)


class RejudgeThread(Thread):
    def __init__(self, user, subsToRejudge):
        super().__init__()
        self.user = user
        self.subsToRejudge = subsToRejudge

    def run(self):
        try:            
            numSubmissions = 0
            for sub in self.subsToRejudge:
                Status.instance().updateRejudgeProgress(numSubmissions)
                runCode(sub, self.user)
                numSubmissions += 1
        finally:
            Status.instance().endRejudge()

@admin_required
def rejudgeAll(request):
    """Ajax method: Rejudge all submissions for problem `id`"""

    user = User.getCurrent(request)
    ctime = time.time() * 1000
    id = request.POST["id"]

    subsToRejudge = [sub for sub in Submission.all() if sub.problem.id == id and sub.timestamp < ctime and sub.result != 'reject']
    if not Status.instance().startRejudge(id, subsToRejudge):
        return JsonResponse("Another rejudge all is still progress. See System Status below to monitor progress.", safe=False)

    RejudgeThread(user, subsToRejudge).start()

    return JsonResponse("Rejudge started. Click System Status below to monitor progress.", safe=False)
   

# Create and return zip of submission data
@admin_required
def download(request):
    id = request.POST["id"]
    submission = Submission.get(id)

    buf = io.BytesIO()
    with ZipFile(buf, 'w') as zip:
        sourceFile = f"source.{exts[submission.language]}"
        zip.writestr(sourceFile, submission.code)

        for index in range(submission.problem.tests):
            for fileType in ["in", "out", "answer", "error"]:
                filename = f"/db/submissions/{id}/{fileType}{index}.txt"
                output_dest_filename = f"{fileType}{index}.txt"
                if os.path.exists(filename):
                    zip.write(filename, output_dest_filename)
                
    data = {"download.zip": base64.b64encode(buf.getvalue()).decode('ascii')}
    
    return JsonResponse(json.dumps(data), safe=False)
