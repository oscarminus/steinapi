#!/usr/bin/python3
# API connector for stein.app

import requests
import re

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
    headers : dict
        Set common headers
    cookie : RequestsCookieJar
        The cookie returned on login
    data : dict
        Basic app data
    userinfo : dict
        Userinformation 
    assets : dict
        The assets of the business unit


    Available methods:
    ------------------
    __init__(self) -> None
    connect(self, user: str, password: str) -> bool
    logout(self) -> bool
    getAppData(self) -> None
    getAssets(self) -> None
    updateAsset(self, id : int, update : dict, notify : bool = False) -> bool

    """
    baseurl = "https://stein.app"
    apiurl = baseurl + "/api/api"
    apikey = str()
    headers = dict()
    cookie = None
    data = dict()
    userinfo = dict()
    assets = dict()



    def __init__(self) -> None:
        """Create the SteinAPI object and set the api endpoint
        """
        # get initial web page and read main java script file
        # extract the api key from the java script file
        r = requests.get(self.baseurl)
        m = re.search(r'<script defer=\"defer\" src=\"([\w\/\.]+)\">', r.text)
        if m:
            js = m.group(1)
            j = requests.get(self.baseurl + "/" + js)
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

    def connect(self, user: str, password: str) -> bool:
        """Create connection and authenticate against stein.api

        Parameters:
        -----------
        user : str
            The user used for authentication
        password : str
            The password used for authentication
        """
        payload = { "username" : user, "password" : password}
        url = self.apiurl + "/login_check"
        r = requests.post(url, headers=self.headers, json=payload)
        self.cookie = r.cookies
        if r.cookies['Token']:
            url = self.apiurl + "/userinfo"
            r = requests.get(url, headers=self.headers, cookies=self.cookie)
            self.userinfo = r.json()
            self.userinfo.update({"bu" : self.userinfo['scope'].split('_')[1]})
            print(self.userinfo)
            return True
        else:
            return False

    def logout(self) -> bool:
        """Logout from stein.app

        Returns:
        --------
        Boolean
            Returns true if logout was successfull
        """
        url = self.apiurl + "/logout"
        r = requests.post(url, headers=self.headers, cookies=self.cookie)
        if r.status_code == 204:
            return True
        else:
            return False

    def getAppData(self) -> None:
        """Retrieves basic app data from stein.app"""
        url = self.apiurl + "/app/data"
        r = requests.get(url, headers=self.headers, cookies=self.cookie)
        self.data = r.json()

    def getAssets(self) -> None:
        """Get assets from stein.app"""
        url = self.apiurl + "/assets?buIds=" + str(self.userinfo['bu'])
        r = requests.get(url, headers=self.headers, cookies=self.cookie)
        self.assets = r.json()

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
        for a in self.assets:
            if a['id'] == id:
                assetdata = a
            
        if assetdata:
            # remove id from the update data. Otherwise we would overwrite another asset
            if "id" in update:
                del update['id']
            data = assetdata | update
            print(data)
            url = self.apiurl + "/assets/" + str(assetdata['id'])
            if notify:
                url = url + "?notifyRadio=true"
            else:
                url = url + "?notifyRadio=false"
            print(url)
            r = requests.patch(url, json=data, headers=self.headers, cookies=self.cookie)
            if r.status_code == 200:
                return True

        return False

if __name__ == "__main__":
    s = SteinAPI()
    s.connect("<user>", "<api>")
    s.getAppData()
    s.getAssets()
    print(s.assets)
#    s.updateAsset(<id>, {"status" : "ready", "comment" : ""})
    s.logout()