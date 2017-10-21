# http://localhost:4074/?code=hasd&hejsan=sd
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import urlparse
import time
import webbrowser
import requests
import requests
import base64
import json
import Keys

playingMusic = False

def MakeGetAuthorizationCodeHandler(OAuth2Class):
    class GetAuthorizationCodeHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return
 
        def do_GET(self):
            parsedPath = urlparse.urlparse(self.path)
           
            for q in parsedPath.query.split("&"):
                kv = q.split("=")
 
                if kv[0] == "code":
                    OAuth2Class.authorizationCode = kv[1]
 
            self.send_response(200)
            self.end_headers()
            self.wfile.write("<script>window.close();</script>")
 
            return
 
    return GetAuthorizationCodeHandler

def MakeGameStateIntegrationHandler(OAuth2Class, deviceId):
    class GetAuthorizationCodeHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return
 
        def do_POST(self):
            global playingMusic

            parsedPath = urlparse.urlparse(self.path)
           
            contentLength = int(self.headers.getheader("content-length", 0))
            body = json.loads(self.rfile.read(contentLength))
 
            shouldBePlay = shouldPlay(body)

            if shouldBePlay and not playingMusic:
                resumeMusic(auth, deviceId)
            elif not shouldBePlay and playingMusic:
                pauseMusic(auth, deviceId)

            playingMusic = shouldBePlay

            self.send_response(200)
            self.end_headers()
            self.wfile.write("<script>window.close();</script>")

            return
 
    return GetAuthorizationCodeHandler
 
class OAuth2:
    def __init__(self, clientId, clientSecret, authorizationURL, tokenURL):
        self.clientId = clientId
        self.clientSecret = clientSecret
 
        self.authorizationURL = authorizationURL
        self.tokenURL = tokenURL
 
        self.authorizationCode = ""
 
    def openAuthorizationURL(self, scopes):
        url = self.getAuthorizationURL(scopes)
        webbrowser.open(url)
 
        return self.getAuthorizationCode()
 
    def getAuthorizationURL(self, scopes):
        return authorizationURL + "?" + "scope=" + " ".join(scopes) + "&response_type=code&client_id=" + self.clientId + "&redirect_uri=http://localhost:4074/"
 
    def getAuthorizationCode(self):
        self.authorizationCode = ""
 
        server = HTTPServer(("", 4074), MakeGetAuthorizationCodeHandler(self))
       
        while self.authorizationCode == "":
            server.handle_request()
 
        return self.authorizationCode
 
    def getTokens(self):
        data = {"grant_type": "authorization_code", "code": self.authorizationCode, "redirect_uri": "http://localhost:4074/"}
        
        r = requests.post(self.tokenURL, data=data, headers={"Authorization": "Basic " + base64.b64encode(self.clientId + ":" + self.clientSecret)})

        return json.loads(r.text)
 
    def getAccessToken(self, secondTry = False):
        if time.time() >= self.expires and not secondTry:
            self.refreshAcessToken()
            return self.getAccessToken(secondTry = True)

        return self.accessToken
 
    def refreshAcessToken(self):
        data = {"grant_type": "refresh_token", "refresh_token": self.refreshToken}
        
        r = requests.post(self.tokenURL, data=data, headers={"Authorization": "Basic " + base64.b64encode(self.clientId + ":" + self.clientSecret)})

        tokens = json.loads(r.text)

        self.accessToken = tokens["access_tokens"]
        self.expires = time.time() + tokens["expires_in"]

    def authorize(self, scopes):
        self.openAuthorizationURL(scopes)
        tokens = self.getTokens()

        self.accessToken = tokens["access_token"]
        self.refreshToken = tokens["refresh_token"]
        self.expires = time.time() + tokens["expires_in"]

def choseDevice():
    devices = getDevices(auth)
    
    print "Select a device"

    i = 1
    for d in devices["devices"]:
        print i, d["name"]
        i += 1
    
    deviceNr = int(raw_input())
    
    if deviceNr > len(devices["devices"]):
        print "Not a valid number"
        exit()

    return devices["devices"][deviceNr - 1]["id"]

def startGSIServer(oauth, deviceId):
    server = HTTPServer(("", 27375), MakeGameStateIntegrationHandler(oauth, deviceId))
    
    server.serve_forever()

def getDevices(oauth2):
    r = requests.get("https://api.spotify.com/v1/me/player/devices", headers={"Accept": "application/json", "Authorization": "Bearer " + oauth2.getAccessToken()})

    return json.loads(r.text)

def shouldPlay(body):
    health = body["player"]["state"]["health"]
    roundPhase = body["round"]["phase"]

    if not body["player"]["steamid"] == body["provider"]["steamid"]:
        return True

    if health > 0 and roundPhase == "live":
        return False

    return True

def pauseMusic(oauth, device):
    print "---------- REQUESTING PAUSE -------------"
    r = requests.put("https://api.spotify.com/v1/me/player/pause?device_id=" + device, headers={"Accept": "application/json", "Authorization": "Bearer " + oauth.getAccessToken()})

def resumeMusic(oauth, device):
    print "---------- REQUESTING RESUME -------------"
    r = requests.put("https://api.spotify.com/v1/me/player/play?device_id=" + device, headers={"Accept": "application/json", "Authorization": "Bearer " + oauth.getAccessToken()})
 
if __name__ == "__main__":
    authorizationURL = "https://accounts.spotify.com/authorize"
    tokenURL = "https://accounts.spotify.com/api/token"
 
    auth = OAuth2(Keys.clientId, Keys.clientSecret, authorizationURL, tokenURL)
    auth.authorize(["user-modify-playback-state", "user-read-playback-state", "user-modify-playback-state"])
    
    startGSIServer(auth, choseDevice())