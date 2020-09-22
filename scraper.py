import sys
import numpy as np
import copy
import random
import os
import time
import pickle
import pandas as pd
import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains

USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246",
                "Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9",
                "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36",
                "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1"]

class Scraper:

    def __init__(self,settings={}):

        self.settings = settings

        self.browser = None
        self.by_url_data = {}
        self.default_soup_parser = "html.parser"
        self.change_user_agent = False

        for setting, value in settings.items():
            if "change_user_agent" in setting: self.change_user_agent = value

    def browser_init(self):

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument(" - incognito")
        #options.add_argument('--user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36"')
        if self.change_user_agent:
            options.add_argument(f'--user-agent="{random.choice(USER_AGENTS)}"')
        self.browser = webdriver.Chrome(executable_path="/usr/bin/chromedriver", chrome_options=options)

    def click_until_element_change(self,xpath,change,type="text"):

        if type == "text":
            no_change = True
            while no_change:
                elem = self.browser.find_element_by_xpath(xpath)
                elem.click()
                if change in elem.text:
                    break
                time.sleep(1.3)

    def get_to_page_bottom(self,wait_=1.9):

        wait_ = random.uniform(wait_,wait_+1.1)
        lenOfPage = self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        match=False
        while(match==False):
            time.sleep(wait_)
            lastCount = lenOfPage
            lenOfPage = self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            if lastCount==lenOfPage:
                match=True

    def scroll_down(self,wait_=2.2):

        lenOfPage = self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        time.sleep(wait_)
        return lenOfPage

    def browser_reset(self):

        self.browser.quit()
        self.browser_init()

class TweetScraper(Scraper):

    def __init__(self,settings={},until_date="2019-04-01",since_date="2020-01-01",tempsave=None):
        Scraper.__init__(self,settings=settings)

        self.tweet_ids = {"_no_results":set([])}
        self.until_date = datetime.datetime.strptime(until_date,"%Y-%m-%d")
        self.since_date = datetime.datetime.strptime(since_date,"%Y-%m-%d")
        self.tempsave = tempsave

        self.default_date_interval = 360

        if self.tempsave is not None:
            self.init_tempsave()

    def set_date_interval(self,interval):

        self.default_date_interval = interval

    def query_to_filename(self,query):

        fname = query
        if "/" in query:
            fname = "({0})".format(fname)
            fname = fname.replace(".","{")
            fname = fname.replace("/","}")

        return fname

    def filename_to_query(self,fname):

        query = fname
        if fname[0] == "(" and fname[-1] == ")":
            query = fname[1:-1]
            query = query.replace("{",".")
            query = query.replace("}","/")

        return query

    def init_tempsave(self):

        if not os.path.exists(self.tempsave):
            os.makedirs(self.tempsave)

        for query_file in os.listdir(self.tempsave):
            if "_no_results" in str(query_file):
                if not "_no_results" in self.tweet_ids:
                    self.tweet_ids["_no_results"]=set([])
                for query in pickle.load(open("{0}{1}".format(self.tempsave,str(query_file)),"rb")):
                    self.tweet_ids["_no_results"].add(query)
            else:
                data = pickle.load(open("{0}{1}".format(self.tempsave,str(query_file)),"rb"))["data"]
                query = self.filename_to_query(str(str(query_file).split(".")[0]))
                if not query in self.tweet_ids:
                    self.tweet_ids[query]=set([])
                self.tweet_ids[query].update(data)

    def dump_tempsave(self,save_specific=None):

        if self.tempsave is not None:
            if save_specific:
                pickle.dump({"since_date":self.since_date,
                "until_date":self.until_date,"data":self.tweet_ids[save_specific]},open('{0}{1}.p'.format(self.tempsave,self.query_to_filename(save_specific)),"wb"))
            else:
                for query in list(self.tweet_ids.keys()):
                    if query != "_no_results":
                        pickle.dump({"since_date":self.since_date,
                        "until_date":self.until_date,"data":self.tweet_ids[query]},open('{0}{1}.p'.format(self.tempsave,self.query_to_filename(query)),"wb"))

            pickle.dump(self.tweet_ids["_no_results"],open("{0}_no_results.p".format(self.tempsave),"wb"))

    def format_tweet_ids_data(self,format,query_list):

        if format == "strict":
            return {k:v for k,v in self.tweet_ids.items() if k in set(query_list)}
        elif format == "single_set":
            single_set = set([])
            for query in list(self.tweet_ids.keys()):
                if query != "_no_results" and query in set(query_list):
                    single_set.update(self.tweet_ids[query])
            return single_set

    def create_date_ranges(self,interval=15):

        date_ranges = []
        current_until_date = self.since_date+datetime.timedelta(days=interval)
        current_since_date = self.since_date
        while current_until_date < self.until_date:
            date_ranges.append((current_since_date,current_until_date-datetime.timedelta(days=1)))
            current_since_date = current_since_date+datetime.timedelta(days=interval)
            current_until_date = current_until_date+datetime.timedelta(days=interval)

        date_ranges.append((current_since_date,self.until_date))
        return date_ranges

    def is_no_results(self):

        no_result = False
        html = self.browser.page_source
        soup = BeautifulSoup(str(html), self.default_soup_parser)
        results = soup.find_all("div",{"class":"css-901oao r-hkyrab r-1qd0xha r-1b6yd1w r-vw2c0b r-ad9z0x r-15d164r r-bcqeeo r-q4m81j r-qvutc0"})
        for box in results:
            if hasattr(box,"text"):
                if "No results for" in str(box.text):
                    no_result = True

        return no_result

    def collect_tweet_ids(self,query):

        tweets_ids_found = set([])
        date_ranges = self.create_date_ranges(interval=self.default_date_interval)
        print (query)
        url = "https://twitter.com/search?f=live&vertical=default&q={query}&src=typd".format(query=query)
        self.browser.get(url)
        time.sleep(random.uniform(2.5,4.2))
        if self.is_no_results():
            return False
        for dr in date_ranges:
            sdate = str(dr[0])[:10]
            udate = str(dr[1])[:10]
            print (str(sdate)+" : "+udate)
            url = "https://twitter.com/search?f=live&vertical=default&q={query}%20since%3A{sdate}%20until%3A{udate}&src=typd".format(query=query,sdate=sdate,udate=udate)
            print (url)
            self.browser_reset()
            self.browser.get(url)
            time.sleep(random.uniform(4.5,7.2))
            wait_ = random.uniform(1.7,1.7+2.1)
            lenOfPage = self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            match=False
            while(match==False):
                time.sleep(wait_)
                lastCount = lenOfPage
                lenOfPage = self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                html = self.browser.page_source
                soup = BeautifulSoup(str(html), self.default_soup_parser)
                results = soup.find_all("div",{"class":"css-1dbjc4n r-1d09ksm r-18u37iz r-1wbh5a2"})
                for result in results:
                    if not "/status/" in str(result): continue
                    tweet_id = str(result).split("/status/")[1].split('"')[0]
                    if tweet_id not in self.tweet_ids[query] and tweet_id not in tweets_ids_found:
                        self.tweet_ids[query].add(tweet_id)
                        tweets_ids_found.add(tweet_id)
                if lastCount==lenOfPage:
                    match=True
            print (len(tweets_ids_found))

        return True

    def get_tweet_ids_from_query_list(self,query_list,format="strict",update=False,no_collect=False):

        #for k in sorted(list(self.tweet_ids.keys())):
            #print (k)
        #print (self.tweet_ids["https://nyadagbladet.se/utrikes/bill-gates-anordnade-stor-coronapandemiovning-manader-innan-det-verkliga-utbrottet/"])
        if no_collect:
            return self.format_tweet_ids_data(format,query_list)

        else:
            self.browser_init()
            for query in query_list:
                if not query in self.tweet_ids:
                    self.tweet_ids[query]=set([])
                if query not in self.tweet_ids["_no_results"]:
                    if not update and query in self.tweet_ids and len(self.tweet_ids[query]) > 0:
                        print ("ALREADY " + query)
                        continue
                    status = self.collect_tweet_ids(query)
                    if not status:
                        self.tweet_ids["_no_results"].add(query)
                    self.dump_tempsave(save_specific=query)
            self.browser.quit()
            return self.format_tweet_ids_data(format,query_list)
