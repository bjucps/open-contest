import time
from datetime import datetime

from django.http import HttpResponse

from contest.auth import logged_in_required
from contest.models.contest import Contest
from contest.models.submission import Submission
from contest.models.user import User
from contest.pages.lib import Page
from contest.pages.lib.htmllib import h1, h, h2, div

all_languages = {
    "c": "C",
    "cpp": "C++",
    "cs": "C#",
    "java": "Java",
    "python3": "Python 3",
    "ruby": "Ruby",
    "vb": "Visual Basic"
}


def leaderboard(request):
    contest = Contest.getCurrent() or Contest.getPast()
    user = User.getCurrent(request)
    if not contest:
        return HttpResponse(Page(
            h1("&nbsp;"),
            h1("No Contest Available", cls="center")
        ))
    elif contest.isScoreboardOff(user):
        return HttpResponse(Page(
            h1("&nbsp;"),
            h1("Scoreboard is off.", cls="center")
        ))

    start = contest.start
    end = contest.end

    subs = get_user_subs_map(contest)
    
    problemSummary = {}
    for prob in contest.problems:
        problemSummary[prob.id] = [0, 0]

    scores = []
    for userid in subs:
        usersubs = subs[userid]
        scor = score(usersubs, contest, problemSummary)

        # Set displayName to fullname if displayFullname option is true,
        # otherwise, use the username
        displayName = User.get(userid).fullname if contest.displayFullname == True else User.get(userid).username
        
        scores.append((
            displayName,
            scor[0],
            scor[1],
            scor[2],
            scor[3]
        ))
    scores = sorted(scores, key=lambda score: score[1] * 1000000000 + score[2] * 10000000 - score[3], reverse=True)
    
    ranks = [i + 1 for i in range(len(scores))]
    rank = 1
    for i in range(len(scores)):
        u1 = scores[i]
        u2 = scores[i - 1] if i > 0 else ('', -1, -1, -1, -1)
        ranks[i] = rank
        if (u1[1], u1[2], u1[3]) != (u2[1], u2[2], u2[3]):
            rank += 1
    
    scoresDisplay = []
    for (name, solved, samples, points, attempts), rank in zip(scores, ranks):
        scoresDisplay.append(h.tr(
            h.td(rank, cls="center"),
            h.td(name),
            h.td(attempts, cls="center"),
            h.td(solved, cls="center"),
            h.td(samples, cls="center"),
            h.td(points, cls="center")
        ))

    problemSummaryDisplay = []
    for problem in contest.problems:
        problemSummaryDisplay.append(h.tr(
            h.td(problem.title),
            h.td(problemSummary[problem.id][0], cls="center"),
            h.td(problemSummary[problem.id][1], cls="center")
        ))

    return HttpResponse(Page(
        h2("Leaderboard", cls="page-title"),
        div(cls="actions", contents=[
            h.button("Detailed Contest Report", cls="button create-message", onclick="window.location.href='/contestreport'")
        ]),
        h.table(cls="banded", contents=[
            h.thead(
                h.tr(
                    h.th("Rank", cls="center"),
                    h.th("User"),
                    h.th("Attempts", cls="center"),
                    h.th("Problems Solved", cls="center"),
                    h.th("Sample Cases Solved", cls="center"),
                    h.th("Penalty Points", cls="center")
                )
            ),
            h.tbody(
                *scoresDisplay
            )
        ]),
        h2("Problem Summary", cls="page-title"),
        h.table(cls="banded", contents=[
            h.thead(
                h.tr(
                    h.th("Problem", cls="center"),
                    h.th("Attempts", cls="center"),
                    h.th("Solved", cls="center"),
                )
            ),
            h.tbody(
                *problemSummaryDisplay
            )
        ]),
        div(cls="align-right", contents=[
            h.br(),
            h.button("Correct Log", cls="button", onclick="window.location='/correctlog'")
        ] if user and user.isAdmin() else []
        )
    ))


def contestreport(request):
    contest = Contest.getCurrent() or Contest.getPast()
    user = User.getCurrent(request)
    if not contest:
        return HttpResponse(Page(
            h1("&nbsp;"),
            h1("No Contest Available", cls="center")
        ))
    elif contest.isScoreboardOff(user):
        return HttpResponse(Page(
            h1("&nbsp;"),
            h1("Scoreboard is off.", cls="center")
        ))

    start = contest.start
    end = contest.end
    problemSummaryreport = []
    
    subs = get_user_subs_map(contest) 

    if start <= time.time() <= end:
        reportcols = [h.th("Rank"), h.th("Contestant"), h.th("Contestant ID"), h.th("Correct"), h.th("Penalty"), ]
    else:
        reportcols = [h.th("Rank"), h.th("Contestant ID"), h.th("Correct"), h.th("Penalty"), ]

    problemSummary = {}
    problems = []
    problemNum = 0
    for prob in contest.problems:
        problemSummary[prob.id] = [0, 0]
        problemNum += 1
        problems.append(prob.id)
        problemSummaryreport.append({"id":prob.id,"title":prob.title,"attempts":0,"correct":0}) 
        reportcols.append(h.th(f"{problemNum}", cls="center"))
    
    scores = []
    for user in subs:
        usersubs = subs[user]
        scor = score(usersubs, contest, problemSummary)
        scores.append((
            User.get(user).username,
            scor[0],
            scor[1],
            scor[2],
            scor[3],
            user
        ))
    
    scores = sorted(scores, key=lambda score: score[1] * 1000000000 + score[2] * 10000000 - score[3], reverse=True)
    ranks = [i + 1 for i in range(len(scores))]
    for i in range(1, len(scores)):
        u1 = scores[i]
        u2 = scores[i - 1]
        if (u1[1], u1[2], u1[3]) == (u2[1], u2[2], u2[3]):
            ranks[i] = ranks[i - 1]

    log = []
    for (name, solved, samples, points, attempts, userid), rank in zip(scores, ranks):
        log.append({"rank": rank, "name": name, "userid": userid, "solved": solved, "points": points})
    
    detailedContestDisplay = []
    for person in log:
        outproblems = []
        submissions = sorted(subs[person["userid"]], key=lambda sub: sub.timestamp) 
        for p in problems:
            p_trys = 0
            earliest_time = 0
            for s in submissions:
                if p == s.problem.id:
                    p_trys += 1
                    if s.result == "ok":
                        earliest_time = s.timestamp
                        break

            if earliest_time: 
                outproblems.append(h.td(f"({p_trys}) {datetime.utcfromtimestamp((earliest_time - start) / 1000).strftime('%H:%M')}"))
                for prob in problemSummaryreport:
                    if prob['id'] == p:
                        prob["attempts"] += p_trys
                        prob["correct"] += 1
                        prob[s.language] = prob.get(s.language, 0) + 1
                        
            elif p_trys:      
                outproblems.append(h.td(f"({p_trys}) -- "))
                for prob in problemSummaryreport:
                    if prob['id'] == p:
                        prob["attempts"] += p_trys
                
            else:
                outproblems.append(h.td(f""))
        
        # Previous logic checked to make sure user was a valid object
        # before retrieving its members. That is why this code does as
        # well
        user = User.getByName(person["name"])
        if user:
            # Set displayName to fullname if displayFullname option is true,
            # otherwise, use the username
            displayName = user.fullname if contest.displayFullname == True else user.username
        else:
            displayName = person["name"]
        
        detailedContestDisplay.append(h.tr(
            h.td(person["rank"]),
            h.td(displayName),
            h.td(person["name"]) if start  <= time.time() <=  end else "",
            h.td(person["solved"]),
            h.td(person["points"]),
            *outproblems
        ))

    lang_col = [h.td("#"), h.td("Title")]
    for lan in all_languages:
        lang_col.append(h.td(all_languages[lan]))
    lang_col.append(h.td("Total Count"))
    problemSummaryDisplay =[]
    LanguageDisplay = []
    i = 0
    for prob in problemSummaryreport:

        i += 1
        problemSummaryDisplay.append(h.tr(
            h.td(i),
            h.td(prob["title"]),
            h.td(prob["attempts"]),
            h.td(prob["correct"]),
        ))

        langcount = []
        total = 0
        for lan in all_languages:
            if lan in prob:
                total += prob[lan]
                langcount.append(h.td(prob[lan]))
            else: langcount.append(h.td(""))

        LanguageDisplay.append(h.tr(
            h.td(i),
            h.td(prob["title"]),
            *langcount,
            h.td(total) if total > 0 else h.td("")
        ))

    return HttpResponse(Page(
        h2("DETAILED STANDINGS", cls="page-title"),
        h.table(cls="banded", contents=[
            h.thead(h.tr(*reportcols)),
            h.tbody(*detailedContestDisplay)
        ]),
        h2("Problem Summary", cls="page-title"),
        h.table(cls="banded", contents=[
            h.thead(
                h.tr(
                    h.td("#"),
                    h.td("Title"),
                    h.td("Attempts"),
                    h.td("Correct")
                )
            ),
            h.tbody(*problemSummaryDisplay)
        ]),
        h2("Language Breakdown", cls="page-title"),
        h.table(cls="banded", contents=[
            h.thead(h.tr(*lang_col)
            ),h.tbody(*LanguageDisplay)
        ]),
        cls='wide-content' # Use a wide format for this page
    ))

def get_user_subs_map(contest: Contest) -> dict:
    contest_prob_ids = [prob.id for prob in contest.problems]
    subs = {}
    for sub in Submission.all():
        if contest.start <= sub.timestamp <= contest.end and not sub.user.isAdmin() and sub.problem.id in contest_prob_ids:
            subs[sub.user.id] = subs.get(sub.user.id, [])
            subs[sub.user.id].append(sub)

    return subs

def score(submissions: list, contest: Contest, problemSummary) -> tuple:
    """ Given a list of submissions by a particular user, calculate that user's score.
        Calculates score in ACM format. """
    solvedProbs = 0
    sampleProbs = 0
    penPoints = 0
    attempts = 0

    # map from problems to list of submissions
    probs = {}

    # Put the submissions into the probs list
    for sub in submissions:
        probId = sub.problem.id
        if probId not in probs:
            probs[probId] = []
        probs[probId].append(sub)
    
    # For each problem, calculate how much it adds to the score
    for prob in probs:
        # Sort the submissions by time
        subs = sorted(probs[prob], key=lambda sub: sub.timestamp)
        # Penalty points for this problem
        points = 0
        solved = False
        sampleSolved = False
        
        for sub in subs:
            attempts += 1

            # If submission not rejected, check to see if the submission was correct for sample data
            if sub.result != "reject":
                for res in sub.results[:sub.problem.samples]:
                    if res != "ok":
                        break
                else:
                    sampleSolved = True

            if sub.result != "ok":
                # Unsuccessful submissions count for 20 penalty points
                # But only if the problem is eventually solved
                points += 20
            else:
                # The first successful submission adds a penalty point for each
                #     minute since the beginning of the contest
                # The timestamp is in millis
                points += (sub.timestamp - contest.start) // 60000
                solved = True
                break
        
        # Increment attempts for problem summary
        problemSummary[sub.problem.id][0] += 1

        # A problem affects the score only if it was successfully solved
        if solved:
            solvedProbs += 1
            penPoints += points
            problemSummary[sub.problem.id][1] += 1
        elif sampleSolved and contest.tieBreaker:
            sampleProbs += 1
    
    # The user's score is dependent on the number of solved problems and the number of penalty points
    return solvedProbs, sampleProbs, int(penPoints), attempts
