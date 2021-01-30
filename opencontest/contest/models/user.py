from uuid import uuid4

from contest.models.simple import setKey, getKey

users = {}
userNames = {}


class User:
    def __init__(self, username: str, fullname: str, password: str, type: str, id: str = None):
        self.id = id
        if username in userNames:
            self.id = userNames[username].id
        self.username = username
        self.password = password
        self.fullname = fullname or "Anonymous"
        self.type = type

    @staticmethod
    def get(id: str):
        if id in users:
            return users[id]
        return None

    @staticmethod
    def getByName(username: str):
        if username in userNames:
            return userNames[username]
        return None
    
    def save(self):
        if self.id == None:
            if self.username in [user.id for user in User.all()]:
                return  # don't create duplicate user
            self.id = self.username
            users[self.id] = self
            userNames[self.username] = self
        usrs = [users[id].toJSON() for id in users]
        setKey("/users.json", usrs)
    
    def toJSON(self):
        return {
            "id": self.id,
            "username": self.username,
            "fullname": self.fullname,
            "password": self.password,
            "type": self.type
        }

    @staticmethod
    def allJSON():
        return [users[id].toJSON() for id in users]
    
    def delete(self):
        del users[self.id]
        del userNames[self.username]
        self.save()
    
    def isAdmin(self) -> bool:
        return self.type == "admin"

    @staticmethod
    def all():
        return [users[id] for id in users]


usrs = getKey("/users.json") or []
for usr in usrs:
    user = User(usr["username"], usr.get('fullname', usr["username"]), usr["password"], usr["type"], usr["id"])
    users[usr["id"]] = user
    userNames[usr["username"]] = user
