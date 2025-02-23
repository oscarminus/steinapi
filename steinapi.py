#!/usr/bin/python3
# API connector for stein.app

import httpx
from http.cookiejar import LWPCookieJar
import re
import logging

COOKIE_FILENAME='/tmp/stein-cookie'

class SteinAPI:
    """Holds the connection to THW stein.app

    Attributes:
    -----------
    baseurl : str
        The stein web page
    apiurl : str
        The api endpoint
    apikey : str
        This might be a key to authenticate the web app, just copied
    buname : str
        The name of the business unit
    bu : dict
        Dictionary holding the data of the business unit
    headers : dict
        Set common headers
    cookie : RequestsCookieJar
        The cookie returned on login
    data : dict
        Basic app data
    userinfo : dict
        Userinformation 
    STATES : dict
        A dict with a translation of the internal used states to human friendly states
    ASSET_FIELDS : dict
        A dict with a translation of the asset fields to human friendly names

    Available methods:
    ------------------
    __init__(self, buname: str) -> None
    connect(self, user: str, password: str) -> bool
    logout(self) -> bool
    getAssets(self) -> None
    updateAsset(self, id : int, update : dict, notify : bool = False) -> bool

    """
    baseurl = "https://stein.app"
    apiurl = baseurl + "/api/api"
    bu = dict()
    buname = ""
    apikey = str()
    headers = dict()
    cookie = None
    data = dict()
    userinfo = dict()
    session = None

    STATES = {"ready": "Einsatzbereit",
          "notready": "Nicht einsatzbereit",
          "semiready": "Bedingt einsatzbereit",
          "inuse": "Im Einsatz",
          "maint": "In der Werkstatt"}

    ASSET_FIELDS = {"category": "Gruppe",
                "comment": "Kommentar",
                "group": "Kategorie",
                "issi": "ISSI",
                "label": "Bezeichnung",
                "plate": "Kennzeichen",
                "radio": "Funkrufname",
                "status": "Status"}



    def __init__(self, buname: str) -> None:
        """Create the SteinAPI object and set the api endpoint
        """
        # get initial web page and read main java script file
        # extract the api key from the java script file
        httpcl = httpx.Client(http2=True)
        r = httpcl.get(self.baseurl)
        m = re.search(r'<script type=\"module\" crossorigin src=\"([\w\/\.\-]+)\"></script>', r.text)
        if m:
            js = m.group(1)
            j = httpcl.get(self.baseurl + "/" + js)
            m = None
            m = re.search(r'headers\.common\[\"X-API-KEY\"]=\"(\w+)\"', j.text)
            if m:
                self.apikey = m.group(1)
                self.headers = { 
                    "accept" : "application/json, text/plain, */*",
                    "content-type" : "application/json",
                    "Pragma" : "no-cache",
                    "Cache-Control" : "no-cache, no-store",
                    "X-API-KEY" : self.apikey}
            else:
                raise ValueError('Could not find API-Key in java script file')
        else:
            raise ValueError('Could not find java script file to determine api key')
        
        self.buname = buname


    def connect(self, user: str, password: str) -> bool:
        """Create connection and authenticate against stein.api

        Parameters:
        -----------
        user : str
            The user used for authentication
        password : str
            The password used for authentication
        """

        # Try to load saved cookie
        cookie_jar = LWPCookieJar(COOKIE_FILENAME)
        try:
            cookie_jar.load()
        except FileNotFoundError:
            pass

        self.session = httpx.Client(http2=True)
        self.session.cookies = cookie_jar

        self.userinfo = self.session.get(self.apiurl + "/userinfo")
        self.userinfo = self.userinfo.json()
        if "name" not in self.userinfo:
            payload = { "username" : user, "password" : password}
            login = self.session.post(self.apiurl + "/login_check", json=payload)
            login.raise_for_status()
            self.userinfo = self.session.get(self.apiurl + "/userinfo")
            self.userinfo = self.userinfo.json()

        self.data = self.session.get(self.apiurl + "/app/data", headers=self.headers, cookies=self.cookie)
        self.data = self.data.json()
        self.bu = next(filter(lambda bu: bu["name"] == self.buname, self.data["bus"]))

        cookie_jar.save(ignore_discard=True)

    def logout(self) -> bool:
        """Logout from stein.app

        Returns:
        --------
        Boolean
            Returns true if logout was successfull
        """
        url = self.apiurl + "/logout"
        r = self.session.post(url, headers=self.headers, cookies=self.cookie)
        if r.status_code == 204:
            return True
        else:
            return False

    def getBuData(self) -> dict:
        """Return the business unit"""
        return self.bu

    def getGroups(self) -> dict:
        """Return groups of assets"""
        return {group["id"]: group["name"] for group in self.data["assetGroups"]}

    def getAssets(self) -> dict:
        """Get assets from stein.app"""
        url = self.apiurl + "/assets/?buIds=" + str(self.bu['id'])
        temp = self.session.get(url, headers=self.headers, cookies=self.cookie)
        return temp.json()

    def updateAsset(self, id : int, update : dict, notify : bool = False) -> bool:
        """Set update asset data

        Parameters:
        -----------
        id : int
            The database id of the asset. This is used as the identifier
        update : dict
            Merge this dict with the old data and do an update this way
        notify : boolean
            Notify the TTB if a vehicle goes to or comes back from the garage 

        Returns:
        --------
        boolean
            Returns true if update was successfull

        {"buId":600,
        "groupId":1,
        "id":xxx,
        "label":"[1] MTW-ZTr",
        "name":"THW-12345",
        "status":"semiready",
        "comment":"Test",
        "category":"ZTr TZ",
        "deleted":false,
        "lastModified":"2022-10-18T13:36:04+02:00",
        "created":"2022-06-23T13:52:21+02:00",
        "lastModifiedBy":"xxx",
        "radioName":"xxx",
        "issi":"xxx",
        "sortOrder":1}
        """

        assetdata = None
        for a in self.getAssets():
            if a['id'] == id:
                assetdata = a
            
        if assetdata:
            # remove id from the update data. Otherwise we would overwrite another asset
            if "id" in update:
                del update['id']
            assetdata.update(update)
            logging.debug("Payload: %s" % str(assetdata))
            url = self.apiurl + "/assets/" + str(assetdata['id'])
            if notify:
                url = url + "?notifyRadio=true"
            else:
                url = url + "?notifyRadio=false"
            logging.debug("Url: %s" % url)
            r = self.session.patch(url, json=assetdata, headers=self.headers, cookies=self.cookie)
            if r.status_code == 200:
                return True
            else:
                logging.warning("Could not set data. Return code was %s, message: %s" % (r.status_code, r.text))
        return False

if __name__ == "__main__":
    s = SteinAPI("Paderborn")
    s.connect("<user>", "<pass>")
    print(s.getAssets())
#    s.updateAsset(<id>, {"status" : "ready", "comment" : ""})
    #s.logout()
