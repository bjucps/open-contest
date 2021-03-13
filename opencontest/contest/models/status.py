import logging


class Status:

    def __init__(self):
        self.rejudgeProgress = ['', 0, 0]     # (problemID, currentIndex, totalToRejudge)

    def isRejudgeInProgress(self):
        return self.rejudgeProgress != ['', 0, 0]

    def startRejudge(self, problemId, subsToRejudge):
        '''Starts a rejudge session, if none is in progress. Returns True if session is started.'''

        if not self.isRejudgeInProgress():  
            # Small possibility of race condition here; no substantial harm if it happens
            self.rejudgeProgress = [problemId, 0, len(subsToRejudge)]
            return True
        else:
            return False

    def updateRejudgeProgress(self, index):
        if self.isRejudgeInProgress():
            self.rejudgeProgress[1] = index

    def endRejudge(self):
        self.rejudgeProgress = ['', 0, 0]

    @staticmethod
    def instance():
        return status

status = Status()