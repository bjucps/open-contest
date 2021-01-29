import time
from uuid import uuid4
from readerwriterlock import rwlock

from contest.models.problem import Problem
from contest.models.simple import getKey, setKey, deleteKey, listSubKeys

lock = rwlock.RWLockWrite()

contests = {}


class Contest:
    saveCallbacks = []

    def __init__(self, id=None):
        if id != None:
            details = getKey(f"/contests/{id}/contest.json")
            self.id = details["id"]
            self.name = details["name"]
            self.start = int(details["start"])   
            self.end = int(details["end"])
            self.scoreboardOff = int(details.get("scoreboardOff", self.end))
            self.showProblInfoBlocks = details.get("showProblInfoBlocks","Off")
            self.problems = [Problem.get(id) for id in details["problems"]]
            self.tieBreaker = str(details.get("tieBreaker", "")) == "true"
            self.displayFullname = details["displayFullname"]

        else:
            self.id = None
            self.name = None
            self.start = None                       # timestamp in milliseconds from time.time() * 1000
            self.end = None
            self.scoreboardOff = None
            self.showProblInfoBlocks = None
            self.problems = None
            self.tieBreaker = False
            self.displayFullname = True

    @staticmethod
    def get(id: uuid4):
        id: str = str(id)
        with lock.gen_rlock():
            if id in contests:
                return contests[id]
            return None
    
    def toJSONSimple(self):
        return {
            "id": self.id,
            "name": self.name,
            "start": self.start,
            "end": self.end,
            "scoreboardOff": self.scoreboardOff,
            "showProblInfoBlocks": self.showProblInfoBlocks,
            "problems": [prob.id for prob in self.problems],            
            "tieBreaker": self.tieBreaker,
            "displayFullname": self.displayFullname
        }

    def save(self):
        with lock.gen_wlock():
            if self.id == None:
                self.id = str(uuid4())
                contests[self.id] = self
            setKey(f"/contests/{self.id}/contest.json", self.toJSONSimple())
        for callback in Contest.saveCallbacks:
            callback(self)
    
    def delete(self):
        with lock.gen_wlock():
            deleteKey(f"/contests/{self.id}")
            del contests[self.id]
    
    def toJSON(self):
        with lock.gen_rlock():
            return {
                "id": self.id,
                "name": self.name,
                "start": self.start,
                "end": self.end,
                "problems": [prob.toJSONSimple() for prob in self.problems],
                "tieBreaker": self.tieBreaker,
                "displayFullname": self.displayFullname
            }

    @staticmethod
    def allJSON():
        with lock.gen_rlock():
            return [contests[id].toJSON() for id in contests]
    
    def forEach(callback: callable):
        with lock.gen_rlock():
            for id in contests:
                callback(contests[id])
    
    def onSave(callback: callable):
        Contest.saveCallbacks.append(callback)

    @staticmethod
    def getCurrent():
        with lock.gen_rlock():
            for id in contests:
                if contests[id].start <= time.time() * 1000 <= contests[id].end:
                    return contests[id]
            return None

    @staticmethod
    def getFuture():
        with lock.gen_rlock():
            contest = None
            for id in contests:
                if contests[id].start > time.time() * 1000:
                    if not contest or contests[id].start < contest.start:
                        contest = contests[id]
            return contest

    @staticmethod
    def getPast():
        with lock.gen_rlock():
            contest = None
            for id in contests:
                if contests[id].end < time.time() * 1000:
                    if not contest or contests[id].end > contest.end:
                        contest = contests[id]
            return contest

    @staticmethod
    def all():
        with lock.gen_rlock():
            return [contests[id] for id in contests]


with lock.gen_wlock():
    for id in listSubKeys("/contests"):
        contests[id] = Contest(id)
