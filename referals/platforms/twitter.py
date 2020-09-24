from TwitterAPI import TwitterAPI
from TwitterAPI import TwitterPager
from random import randint
import os
import time
import urllib.request
import json
import sys
from urllib.error import HTTPError
from requests_oauthlib import OAuth1
from _csv import reader
from referals.scraper.scraper import TweetScraper
import referals.utils.helpers as hlp

class Twitter:

    def __init__(self,api_keys=[]):

        self.tempsave = "twitter_tempsaves/"
        self.api_keys = api_keys

        self.api_keys = [TwitterAPI(*k) for k in self.api_keys]

    def call_api(self,apilist,query_type,query_settings={},wait=0.0):
        if wait > 0: time.sleep(wait)
        succes = False
        while succes == False:
            #if True:
            try:
                api_key = apilist[randint(0,len(apilist)-1)]
                pager = api_key.request(query_type,query_settings)
                succes = True
                return pager
            except Exception as e:
                print ("recalling query...")
                time.sleep(2)

    def get_iterator(self,pager,query_type,query_settings={},wait=0.0):

        recall_count = 0
        succes = False
        while succes == False:
            try:
                iter_ = pager.get_iterator()
                succes = True
                return iter_
            except Exception as ex1:
                if "request failed (401)" in str(ex1) or "request failed (404)" in str(ex1):
                    print ("cannot follow through on query: {0} - {1}".format(query_type,str(query_settings)))
                    return False
                elif "failed (403)" in str(ex1):
                    return False
                recall_count+=1
                if recall_count > 3:
                    print ("*** restarting ***")
                    time.sleep(55)
                    pager = self.call_api(self.api_keys,query_type,query_settings=query_settings,wait=wait)
                    time.sleep(55)
                    try:
                        iter_ = pager.get_iterator()
                        return iter_
                    except Exception as ex2:
                        print (ex2)
                        print ("Manual restart needed")
                        sys.exit()
                print ("recalling iterator... > {0}".format(ex1))
                time.sleep(2)

    def render_to_json(self,graph_url):
        #render graph url call to JSON
        tempG = graph_url
        tempB = False
        tempN = 0

        while tempN < 10:
            try:
                web_response = urllib.request.urlopen(tempG, timeout=30)
                if tempN > 1:
                    return {'data':['bad_request']}
                else:
                    pass
                readable_page = web_response.read().decode('utf-8')
                json_data = json.loads(readable_page)
                return json_data
                tempB = True
                tempN = 100
            except:
                tempB = False
                print ("recalling..... " + str(tempG))
                time.sleep(5)
                tempN+=1

        return []

    def get_url_from_tweet_data(self,tweet,url,return_type="first"):
        urls = None
        if "entities" in tweet:
            entities = tweet["entities"]
            if 'urls' in entities:
                if 'retweeted_status' in tweet and "entities" in tweet["retweeted_status"] and "urls" in tweet["retweeted_status"]["entities"]:
                    entities["urls"].extend(tweet["retweeted_status"]["entities"]["urls"])
                if len (entities['urls']) > 0:
                    urls = []
                    for obj in entities['urls']:
                        if "twitter." not in obj["expanded_url"]:
                            txt = obj['expanded_url']
                            urls.append(txt)

        if urls is None or len(urls) == 0:
            urls = [url]
        if return_type == "first":
            return urls[0]
        elif return_type == "list":
            return urls
        elif return_type == "str":
            return str(urls).replace("[","").replace("]","")

    def create_referal_data(self,tweet,url):

        post_url = "https://twitter.com/{0}/status/{1}".format(tweet["user"]["screen_name"],tweet["id"])
        tweet_url = self.get_url_from_tweet_data(tweet,url,return_type="first")
        referal_data = {"link_id":url, "total_reactions_count":tweet["favorite_count"],
                "page_size":tweet["user"]["followers_count"], "retweets":tweet["retweet_count"],
                "link":tweet_url,"message":tweet["full_text"],
                "post_url":post_url,
                "name":tweet["user"]["name"],"profile_image_url":tweet["user"]["profile_image_url"],
                "post_date":hlp.datetime_str_to_cet(tweet["created_at"][:19],'%a %b %d %H:%M:%S'),"type_id":5}

        return referal_data

    def get_tweet_objects_from_ids(self,id_list):

        query_settings={"id":str(id_list).replace("[","").replace("]","").replace("'","").replace(" ",""),"include_entities":"true","tweet_mode":"extended"}
        query = "statuses/lookup"
        tweet_pager = self.call_api(self.api_keys,query,query_settings=query_settings)
        iter_ = self.get_iterator(tweet_pager,query,query_settings=query_settings)

        return iter_

    def get_retweet_objects_from_id(self,id_):

        query_settings={"id":id_,"count":"100","trim_user":"false","tweet_mode":"extended"}
        query = "statuses/retweets/:{0}".format(id_)
        tweet_pager = self.call_api(self.api_keys,query,query_settings=query_settings)
        iter_ = self.get_iterator(tweet_pager,query,query_settings=query_settings)
        time.sleep(1.1)

        return iter_

    def get_url_referals(self,url,include_retweets=False):

        l = []
        tws = TweetScraper(settings={},until_date="2020-08-25",since_date="2020-02-01",tempsave=self.tempsave)
        tweet_ids = tws.get_tweet_ids_from_query_list([url],format="single_set",update=False)
        parsed_ids = set([])
        for id_list in hlp.chunks(list(tweet_ids),100):
            tweets = self.get_tweet_objects_from_ids(id_list)
            for row in tweets:
                referal_data = self.create_referal_data(row,url)

                if include_retweets:
                    if referal_data["retweets"]>0:
                        retweets = self.get_retweet_objects_from_id(row["id"])
                        for rrow in retweets:
                            referal_data = self.create_referal_data(rrow,url)
                            if rrow["id"] not in parsed_ids:
                                l.append(referal_data)
                                parsed_ids.add(rrow["id"])
                if row["id"] not in parsed_ids:
                    l.append(referal_data)
                    parsed_ids.add(row["id"])

        return l
