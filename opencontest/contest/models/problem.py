from uuid import uuid4
from readerwriterlock import rwlock

from contest.models.simple import getKey, setKey, deleteKey, listSubKeys

lock = rwlock.RWLockWrite()

problems = {}


class Datum:
    def __init__(self, input, output):
        self.input = input
        self.output = output
    
    def get(id: str, num: int):
        input = getKey(f"/problems/{id}/input/in{num}.txt", False).replace("\r", "")
        output = getKey(f"/problems/{id}/output/out{num}.txt", False).replace("\r", "")
        return Datum(input, output)
    
    def toJSON(self):
        return {
            "input": self.input,
            "output": self.output
        }


class Problem:
    default_timelimit = 5
    saveCallbacks = []

    def __init__(self, id=None):
        if id != None:
            details = getKey(f"/problems/{id}/problem.json")
            self.id = details["id"]
            self.title = details["title"]
            self.description = details["description"]
            self.statement = details["statement"]
            self.input = details["input"]
            self.output = details["output"]
            self.constraints = details["constraints"]
            self.samples = int(details["samples"])  # Number of sample test cases
            self.tests = int(details["tests"])    # Total number of test cases
            self.sampleData = [Datum.get(id, i) for i in range(self.samples)]
            self.testData = [Datum.get(id, i) for i in range(self.tests)]
            self.timelimit = details.get("timelimit", str(Problem.default_timelimit))  # Time limit in seconds
        else:
            self.id = None
            self.title = None
            self.description = None
            self.statement = None
            self.input = None
            self.output = None
            self.constraints = None
            self.samples = 0
            self.tests = 0
            self.sampleData = []
            self.testData = []
            self.timelimit = str(Problem.default_timelimit)

    @staticmethod
    def get(id: str):
        if not id:
            return None

        with lock.gen_rlock():
            if id in problems:
                return problems[id]
            raise Exception(f"No problem with id '{id}' in the database")
    
    def toJSONSimple(self):
        return {
            "id":          self.id,
            "title":       self.title,
            "description": self.description,
            "statement":   self.statement,
            "input":       self.input,
            "output":      self.output,
            "constraints": self.constraints,
            "samples":     self.samples,
            "tests":       self.tests,
            "timelimit":   self.timelimit
        }

    def save(self):
        with lock.gen_wlock():
            if self.id == None:
                self.id = str(uuid4())
                problems[self.id] = self
            setKey(f"/problems/{self.id}/problem.json", self.toJSONSimple())
            for i, datum in enumerate(self.testData):
                setKey(f"/problems/{self.id}/input/in{i}.txt", datum.input)
                setKey(f"/problems/{self.id}/output/out{i}.txt", datum.output)
            self.sampleData = [Datum.get(self.id, i) for i in range(self.samples)]

        for callback in Problem.saveCallbacks:
            callback(self)
    
    def delete(self):
        with lock.gen_wlock():
            deleteKey(f"/problems/{self.id}")
            del problems[self.id]
        
    def toJSON(self):
        with lock.gen_rlock():
            json = self.toJSONSimple()
            json["sampleData"] = [datum.toJSON() for datum in self.sampleData]
            return json
    
    def toJSONFull(self):
        json = self.toJSONSimple()
        json["testData"] = [datum.toJSON() for datum in self.testData]
        return json

    @staticmethod
    def allJSON():
        with lock.gen_rlock():
            return [problems[id].toJSONSimple() for id in problems]
    
    def forEach(callback: callable):
        with lock.gen_rlock():
            for id in sorted(problems.keys(), key=lambda probid: problems[probid].title):
                callback(problems[id])
    
    def onSave(callback: callable):
        Problem.saveCallbacks.append(callback)

    @staticmethod
    def all():
        with lock.gen_rlock():
            return [problems[id] for id in problems]


with lock.gen_wlock():
    for id in listSubKeys("/problems"):
        problems[id] = Problem(id)
