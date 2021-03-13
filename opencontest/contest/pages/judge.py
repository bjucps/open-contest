import logging, difflib, re
from bs4 import BeautifulSoup

from django.http import HttpResponse, JsonResponse

from contest.auth import admin_required
from contest.models.contest import Contest
from contest.models.submission import Submission
from contest.models.problem import Problem
from contest.models.user import User
from contest.models.status import Status
from contest.pages.lib import Page
from contest.pages.lib.htmllib import UIElement, h, div, code_encode, h1, h2

from opencontest.settings import OC_MAX_CONCURRENT_SUBMISSIONS


logger = logging.getLogger(__name__)

class ProblemTab(UIElement):
    def __init__(self, x):
        num, prob = x
        self.html = h.li(
            h.a(prob.title, href=f"#tabs-{num}")
        )


icons = {
    "ok": "check",
    "wrong_answer": "times",
    "tle": "clock",
    "runtime_error": "exclamation-triangle",
    "presentation_error": "times",
    "extra_output": "times",
    "incomplete_output": "times",
    "reject": "times",
    "pending": "sync",
    "pending_review": "sync",
}
verdict_name = {
    "ok": "Accepted",
    "wrong_answer": "Wrong Answer",
    "tle": "Time Limit Exceeded",
    "runtime_error": "Runtime Error",
    "presentation_error": "Presentation Error",
    "extra_output": "Extra Output",
    "incomplete_output": "Incomplete Output",
    "reject": "Submission Rejected",
    "pending": "Executing ...",
    "pending_review": "Pending Review",
}


def resultOptions(result):
    ans = []
    for res in verdict_name:
        if res == Submission.RESULT_PENDING or res == Submission.RESULT_PENDING_REVIEW:
            pass  # These should not appear as choices in the dropdown
        elif result == res:
            ans.append(h.option(verdict_name[res], value=res, selected="selected"))
        else:
            ans.append(h.option(verdict_name[res], value=res))
    return ans


def statusOptions(status):
    ans = []
    for stat in [Submission.STATUS_REVIEW, Submission.STATUS_JUDGED]:
        if status == stat:
            ans.append(h.option((stat), value=stat, selected="selected"))
        else:
            ans.append(h.option((stat), value=stat))
    return ans


class TestCaseTab(UIElement):
    def __init__(self, x, sub):
        num, result = x
        test_label = "Sample" if num < sub.problem.samples else "Judge"
        self.html = h.li(
            h.a(href=f"#tabs-{sub.id}-{num}", contents=[
                h.i(cls=f"fa fa-{icons[result]}", title=f"{verdict_name[result]}"),
                f"{test_label} #{num}"
            ])
        )


class TestCaseData(UIElement):
    def __init__(self, x, sub):
        num, input, output, error, answer = x
        if input == None: input = "" 
        if output == None: output = "" 
        if error == None: error = ""
        
        contents=[
            div(cls="row", id="judge-viewDiffButton", contents=[
                div(cls="col-12", contents=[
                    h.button(
                        "View Diff",
                        onclick=f"window.open('viewDiff/{sub.id}#case{num}diff', '_blank');",
                        target="_blank",
                    )
                ])
            ]),
            div(cls="row", contents=[
                div(cls="col-12", contents=[
                    h.h4("Input"),
                    h.code(code_encode(input))
                ])
            ]),
            div(cls="row", contents=[
                div(cls="col-6", contents=[
                    h.h4("Output"),
                    h.code(code_encode(output))
                ]),
                div(cls="col-6", contents=[
                    h.h4("Correct Answer"),
                    h.code(code_encode(answer))
                ])
            ]),
        ]

        if error != "":
            contents.append(
                div(cls="row", contents=[
                    div(cls="col-12", contents=[
                        h.h4("Standard Error"),
                        h.code(code_encode(error))
                    ])
                ]),
            )

        self.html = div(id=f"tabs-{sub.id}-{num}", contents=contents)


class SubmissionCard(UIElement):
    def __init__(self, submission: Submission, user, force):
        subTime = submission.timestamp
        probName = submission.problem.title
        cls = "red" if submission.result != "ok" else ""
        self.html = div(cls="modal-content", contents=[
            div(cls=f"modal-header {cls}", contents=[
                h.h5(
                    f"{probName} from {submission.user.username} at ",
                    h.span(subTime, cls="time-format"),
                    f" (id {submission.id})",
                ),
                """
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>"""
            ]),
            div(cls="modal-body", contents=[
                h.input(type="hidden", id="version", value=f"{submission.version}"),
                h.strong("Result: ",
                    h.select(cls=f"result-choice {submission.id}", contents=[
                        *resultOptions(submission.result)
                    ])
                ),
                h.strong("&emsp;Status: ",
                    h.select(cls=f"status-choice {submission.id}", contents=[
                        *statusOptions(submission.status)
                    ])
                ),
                h.span("&emsp;"),
                h.button("Save", type="button", onclick=f"changeSubmissionResult('{submission.id}', '{submission.version}')", cls="btn btn-primary"),
                h.span(" "),
                h.button("Retest", type="button", onclick=f"rejudge('{submission.id}')", cls="btn btn-primary rejudge"),
                h.span(" "),
                h.button("Download", type="button", onclick=f"download('{submission.id}')", cls="btn btn-primary rejudge"),
                h.br(),
                h.br(),
                h.strong(f"Language: <span class='language-format'>{submission.language}</span>"),
                h.code(code_encode(submission.code), cls="code"),
                div(cls="result-tabs", id="result-tabs", contents=[
                    h.ul(*map(lambda x: TestCaseTab(x, submission), enumerate(submission.results))),
                    *map(lambda x: TestCaseData(x, submission), zip(range(submission.problem.tests), 
                        submission.readFilesForDisplay('in'), submission.readFilesForDisplay('out'), 
                        submission.readFilesForDisplay('error'), submission.readFilesForDisplay('answer')))
                ])
            ])
        ])


class ProblemContent(UIElement):
    def __init__(self, x, cont):
        num, prob = x
        subs = filter(lambda sub: sub.problem == prob and cont.start <= sub.timestamp <= cont.end, Submission.all())
        self.html = div(*map(SubmissionCard, subs), id=f"tabs-{num}")


class SubmissionRow(UIElement):
    def __init__(self, sub):
        checkoutUser = User.get(sub.checkout)
        self.html = h.tr(
            h.td(sub.user.username),
            h.td(sub.problem.title),
            h.td(sub.id), # cls='time-format', contents=sub.timestamp
            h.td(sub.language),
            h.td(
                h.i("&nbsp;", cls=f"fa fa-{icons.get(sub.result)}"),
                h.span(verdict_name.get(sub.result))
            ),
            h.td(contents=[
                sub.status,
                h.p(sub.version, id=f"{sub.id}-version", hidden=True)
            ]),
            h.td(checkoutUser.username if checkoutUser is not None else "None"),
            id=sub.id,
            cls="submit-row",
        )


class SubmissionTable(UIElement):
    def __init__(self, contest):
        subs = sorted(
            filter(lambda sub: sub.user.type != "admin" and contest.start <= sub.timestamp <= contest.end, Submission.all()),
            key=lambda s: s.timestamp)

        self.html = h.table(
            h.thead(
                h.tr(
                    h.th("Contestant"),
                    h.th("Problem"),
                    h.th("Id"),
                    h.th("Language"),
                    h.th("Result"),
                    h.th("Status"),
                    h.th("Checkout"),
                )
            ),
            h.tbody(
                *map(lambda sub: SubmissionRow(sub), subs)
            ),
            id="submissions"
        )


@admin_required
def judge(request):
    cont = Contest.getCurrent() or Contest.getPast()
    if not cont:
        return HttpResponse(Page(
            h1("&nbsp;"),
            h1("No Contest Available", cls="center")
        ))
    return HttpResponse(Page(
        h2("Judge Submissions", cls="page-title judge-width"),
        div(id="judge-table", cls="judge-width", contents=[
            SubmissionTable(cont)
        ]),
        div(cls="modal", tabindex="-1", role="dialog", contents=[
            div(cls="modal-dialog", role="document", contents=[
                div(id="modal-content")
            ])
        ]),
        cls='wide-content' # Use a wide format for this page
    ))

def systemStatus(request):
    contestName = Contest.getCurrent().name if Contest.getCurrent() else "None"
    submissionsTesting = OC_MAX_CONCURRENT_SUBMISSIONS - Submission.runningSubmissions._value
    if Status.instance().isRejudgeInProgress():
        progress = Status.instance().rejudgeProgress
        problem = Problem.get(progress[0])
        rejudgeProgress = f"Rejudged {progress[1]} of {progress[2]} submissions of {problem.title}"
    else:
        rejudgeProgress = "none"

    return HttpResponse(Page(
        h2("System Status", cls="page-title"),
        h.table(
            h.tr(
                h.th("Current contest:"),
                h.td(contestName)
            ),
            h.tr(
                h.th("Submissions testing:"),
                h.td(submissionsTesting)
            ),
            h.tr(
                h.th("Rejudge progress:"),
                h.td(rejudgeProgress)
            ),
        )
    ))
    

@admin_required
def judge_submission(request, *args, **kwargs):    
    submission = Submission.get(kwargs.get('id'))
    user = User.getCurrent(request)
    version = int(request.POST["version"])
    force = kwargs.get('force') == "force"
    if submission.version != version:
        return JsonResponse(f"CHANGES", safe=False)
    elif not submission.checkoutToJudge(user.id, force):
        return JsonResponse(f"CONFLICT:{User.get(submission.checkout).username}", safe=False)
    return HttpResponse(SubmissionCard(submission, user, force))


def judge_submission_close(request):
    submission = Submission.get(request.POST["id"])
    user = User.getCurrent(request)
    if submission.checkout == user.id:
        submission.checkout = None
    return JsonResponse('ok', safe=False)

def generateDiffTable(original: str, output: str) -> str:
    """Generate a HTML diff table given two strings
    
    original -- the original string
    
    output -- the string to compare to the original to detect changes
    """
    
    # Create a HtmlDiff object to create our table
    hd = difflib.HtmlDiff(wrapcolumn=100)

    # Create the table
    table = hd.make_table(
        original.split("\n"),   # Split both strings because make_table
        output.split("\n")      # takes a list of strings for each argument
    )

    # Remove extra columns
    r = re.compile("<td class=\"diff_next\".*?</td>")
    test = r.findall(table)
    for i in test:
        table = table.replace(i, "")
    
    table = BeautifulSoup(table, "html.parser")

    # Iterate over every row in the table
    for row in table.find_all("tr"):

        # Get the 2nd and 4th columns which contain
        # the actual diffs
        colNo = 0
        expected = None
        output = None
        for cell in row:
            if colNo == 1:
                expected = cell
            elif colNo == 3:
                output = cell
            colNo += 1

        expected['style'] = "width:47%"
        output['style'] = "width:47%"

        # Highlight both rows if there was a diff found
        # in both columns (a diff will have a <span>
        # child element if a change was found)
        if expected.find('span') and output.find('span'):
            expected['class'] = "diff_remove"
            output['class'] = "diff_insert"
        
        # Highlight the right column with green and the
        # other column with gray if there was only an
        # insert
        elif output.find('span'):
            output['class'] = "diff_insert"
            expected['class'] = "diff_blank"
        
        # Highlight the left column with green and the
        # other column with gray if there was only a
        # deletion
        elif expected.find('span'):
            expected['class'] = "diff_insert"
            output['class'] = "diff_blank"

    return table.decode_contents()

@admin_required
def viewDiff(request, *args, **kwargs):
    submission = Submission.get(kwargs.get('id'))
    user = User.getCurrent(request)
    problem = submission.problem

    answers = submission.readFilesForDisplay('out')

    diffTables = []
    for i in range(len(problem.testData)):
        if i < problem.samples:
            caseType = "Sample"
            caseNo = i
        else:
            caseType = "Judge"
            caseNo = i - problem.samples

        diffTables.append(
            h.div(
                h.h3(f"{caseType} Case #{caseNo} (Expected Output | Contestant Output)",id=f"case{i}diff"),
                h.div(
                    h.script(f"document.getElementById('case{i}result').innerHTML = 'Result: ' + verdict_name.{submission.results[i]}"),
                    id=f"case{i}result",
                ),
                generateDiffTable(problem.testData[i].output, answers[i]),
            ))
        pass
    
    return HttpResponse(
        div(cls="center", contents=[

            h.link(rel="stylesheet", href="/static/styles/style.css?642ab0bc-f075-4c4c-a2ba-00f55392dafc", type="text/css"),

            h.script(src="/static/lib/jquery/jquery.min.js"),
            h.script(src="/static/lib/jqueryui/jquery-ui.min.js"),
            h.script(src="/static/scripts/script.js?75c1bf1e-10e8-4c8d-9730-0903f6540439"),

            h2(f"Diffs for {submission.id}", cls="center"),
            
            h.em("Insertions are in <span style=color:darkgreen;background-color:palegreen>green</span>, deletions are in <span style=color:darkred;background-color:#F6B0B0>red</span>"),

            h.div(contents=diffTables)
        ]))