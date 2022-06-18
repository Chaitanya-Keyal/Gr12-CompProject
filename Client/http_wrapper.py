import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


class Http:
    POST = "post"
    GET = "get"
    PUT = "put"
    DELETE = "delete"

    def __init__(self, address):
        self.address = address
        self.TOKEN = None

    def login_signup(self, method, username, password, remember_me=False):
        data = {"username": username, "password": password}
        r = self.send(Http.POST, method, data=data)
        if r.status_code == 200:
            if method == "login":
                self.TOKEN = r.json()["Token"]
                if remember_me:
                    return r.json()["Password"]
            return 1
        elif r.status_code == 406:
            return -1
        return 0

    def login(self, username, password, remember_me=False, remember_login=False):
        if remember_login:
            data = {"username": username, "password": password}
            r = self.send(Http.POST, "remember_login", data=data)
            if r.status_code == 200:
                self.TOKEN = r.json()["Token"]
                return 1
            elif r.status_code == 406:
                return -1
            return 0
        return self.login_signup("login", username, password, remember_me=remember_me)

    def register(self, username, password):
        return self.login_signup("register", username, password)

    def del_user(self):
        path = "delete_user"
        r = self.auth_send(Http.DELETE, path)
        if r.status_code != 200:
            return False
        return True

    def logout(self):
        path = "logout"
        r = self.auth_send(Http.POST, path)
        if r.status_code != 200:
            return False
        return True

    def mply_details(self, pos=None):
        path = "details"
        if pos != None:
            path += "/" + str(pos)
        r = self.game_send(Http.GET, "monopoly", path)
        if r.status_code == 404:
            return -1
        elif r.status_code != 200:
            return False
        else:
            return r.json()

    def addgame(self, game, winner, result, players):
        res = {str(i): str(result[i]) for i in result}
        r = self.game_send(
            "post",
            game,
            "add_game",
            {"winner": winner, "result": res, "players": players},
        )
        return r.json()

    def stats(self, game, uuid):
        r = self.game_send("get", game, f"stats/{uuid}")
        return r.json()

    def leaderboard(self, game):
        r = self.game_send("get", game, f"leaderboard")
        return r.json()

    def game_send(self, method, game, path, data=None):
        path = f"{game}/{path}"
        r = self.auth_send(method, path, data)
        return r

    def auth_send(self, method, path, data=None):
        if not self.TOKEN:
            return Response(400, "Please Login")

        headers = {"Authorization": "Bearer " + self.TOKEN}
        r = self.send(method, path, data, headers=headers)
        return r

    def send(self, method, path, data=None, headers={}):
        url = self.address + "/" + path
        r = None

        if method == "post":
            r = requests.post(url, json=data, headers=headers, verify=False)
        elif method == "put":
            r = requests.put(url, json=data, headers=headers, verify=False)
        elif method == "get":
            r = requests.get(url, headers=headers, verify=False)
        elif method == "delete":
            r = requests.delete(url, headers=headers, verify=False)
        else:
            return "INVALID REQUEST"
        return r


class Response:
    def __init__(self, code, body):
        self.status_code = code
        self.body = body

    def json(self):
        return self.body


if __name__ == "__main__":
    app = Http("http://localhost:5000")
    print(app.login("test", "test"))
    print(app.leaderboard("chess"))
    # print(app.addgame("chess", 1, {1: 2}, [1, 32]))
    # print(app.stats("monopoly", 1))
    # print(app.del_user())
