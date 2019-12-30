from django.urls import path

from contest.UIElements.pages.contests import listContests, editContest
from contest.UIElements.pages.messages import displayMessages
from contest.UIElements.pages.problemDisplay import listProblems, viewProblem
from contest.UIElements.pages.problemEdit import editProblem, newProblem, listProblemsAdmin
from contest.UIElements.pages.static import setup
from contest.UIElements.pages.users import getUsers
from contest.views.contests import deleteContest, createContest
from contest.views.generic import login, root, logout
from contest.views.messages import getMessages, sendMessage
from contest.views.problems import deleteProblem, createProblem
from contest.views.users import createUser, deleteUser

app_name = 'contest'
urlpatterns = [
    path('login', login, name='login'),
    path('logout', logout, name='logout'),
    path('getMessages', getMessages, name='getMessages'),
    path('sendMessage', sendMessage, name='sendMessage'),
    path('messages/<uuid:id>', displayMessages, name='displayMessages'),
    path('messages/inbox', displayMessages, name='inbox'),
    path('messages/processed', displayMessages, name='processed'),
    path('messages/announcements', displayMessages, name='announcements'),

    # logged in required
    path('', root, name='root'),
    path('problems', listProblems, name='listProblems'),
    path('problems/<uuid:id>', viewProblem, name='viewProblem'),

    # admin
    path('setup', setup, name='setup'),

    path('contests', listContests, name='listContests'),
    path('contests/<uuid:id>', editContest, name='editContestAdmin'),
    path('editContest', createContest, name='saveNewContest'),
    path('contests/new', editContest, name='createNewContest'),
    path('deleteContest', deleteContest, name='deleteContest'),

    path('problems_mgmt', listProblemsAdmin, name='adminListProblems'),
    path('problems/new', newProblem, name='newProblem'),
    path('problems/<uuid:id>/edit', editProblem, name='editProblem'),
    path('editProblem', createProblem, name='anotherEditProblem'),
    path('deleteProblem', deleteProblem, name='deleteProblem'),

    path('users', getUsers, name='getUsers'),
    path('createUser', createUser, name='createUser'),
    path('deleteUser', deleteUser, name='deleteUser')
]