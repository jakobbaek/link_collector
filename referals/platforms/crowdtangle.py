import random
import requests
import time

class Crowdtangle:

    def __init__(self,api_tokens=[]):

        self.api_tokens = api_tokens

        self.apiBaseUrl = "https://api.crowdtangle.com/ce/"
        self.chromeAppVersion = "3.0.3"
        self.userAgent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"

    def _requestAPI(self,requestUrl, params, link):
        headers = ({'User-Agent': self.userAgent,\
        'Accept': 'application/json, text/javascript, */*; q=0.01',\
        'Sec-Fetch-Mode': 'cors'})
        params['link'] = link
        result = requests.get(requestUrl, params = params, headers=headers)
        return result

    def _getReferalSection(self,url):
        requestUrl = self.apiBaseUrl + "links"
        referalParams = {
            "token": random.choice(self.api_tokens),"version": self.chromeAppVersion}
        result = self._requestAPI(requestUrl, referalParams, url)

        if(result.status_code == 500):
            print("ERROR 500:")
            print(result.headers)
            result = self._requestAPI(requestUrl, referalParams, url)

            if(result.status_code == 500):
                print("ERROR 500:")
                print(result.headers)
        return result.json()

    def get_url_referals(self,url,wait=15):

        time.sleep(wait)
        data = self._getReferalSection(url)
        if "error" not in data and 'result' in data:
            l = []
            data['result']['posts']['posts'].sort(key = lambda x:x['post_date']) #sort datetime
            for post in data['result']['posts']['posts']:
                post["link_id"]=url
                l.append(post)
        else:
            print("No referal data :(, link : " +str(url))

        return l
