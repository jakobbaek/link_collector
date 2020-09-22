from urllib.parse import urlparse
import requests
import re
import random
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import signal
import timeout_decorator
from timeout_decorator import TimeoutError
from scraper import Scraper, USER_AGENTS

COMMON_SHORTERNERS = set(["http://bit.ly/","https://bit.ly/","http://tinyurl.com/","https://tinyurl.com/",
                        "http://goo.gl/","https://goo.gl/","https://t.co/","http://t.co/"])

COMMON_PROBLEMS = set([".mp4"])

class LinkUtils:

    def __init__(self):

        pass

    @staticmethod
    def single_clean_url(url):

        new_url = str(url)
        if "&fbclid" in new_url: new_url = new_url.split("&fbclid")[0]
        if "?fbclid" in new_url: new_url = new_url.split("?fbclid")[0]
        if "&ocid=" in new_url: new_url = new_url.split("&ocid=")[0]
        if "?ocid=" in new_url: new_url = new_url.split("?ocid=")[0]
        if "&feature=youtu.be" in new_url: new_url = new_url.split("&feature=youtu.be")[0]
        if "?feature=youtu.be" in new_url: new_url = new_url.split("?feature=youtu.be")[0]
        if "&feature=" in new_url: new_url = new_url.split("&feature=")[0]
        if "?feature=" in new_url: new_url = new_url.split("?feature=")[0]
        if "&r=" in new_url: new_url = new_url.split("&r=")[0]
        if "?r=" in new_url: new_url = new_url.split("?r=")[0]
        if "&s=" in new_url: new_url = new_url.split("&s=")[0]
        if "?s=" in new_url: new_url = new_url.split("?s=")[0]
        if "&cid_source" in new_url: new_url = new_url.split("&cid_source")[0]
        if "?cid_source" in new_url: new_url = new_url.split("?cid_source")[0]
        if "&utm_source" in new_url: new_url = new_url.split("&utm_source")[0]
        if "?utm_source" in new_url: new_url = new_url.split("?utm_source")[0]
        if "&recruiter=" in new_url: new_url = new_url.split("&recruiter=")[0]
        if "?recruiter=" in new_url: new_url = new_url.split("?recruiter=")[0]

        if str(new_url)[-1] == "/": new_url = str(new_url)[:-1]

        return new_url

    @classmethod
    def _recursive_trim(self,url):

        while url[-1].isalnum() == False:
            url = url[:-1]
        return url

    @classmethod
    def signal_handler(self, signum, frame):
        return 1

    @classmethod
    def get_url_list_from_text(cls,inp_text):

        new_inp_text = inp_text
        urls = []
        while True:
            urls_attached = len(urls)
            for s_string in ["(?P<url>https?://[^\s]+)","(?P<url>http?://[^\s]+)","(?P<url>www?.[^\s]+)"]:
                try:
                    found_url = re.search(s_string, new_inp_text)
                except Exception as e:
                    print (e)
                    found_url = None
                if found_url is not None:
                    real_url = found_url.group("url")
                    urls.append(real_url)
                    new_inp_text = new_inp_text.replace(str(real_url),"")
            if len(urls) <= urls_attached:
                break
        return urls

    @classmethod
    def remove_url_prefix(cls,url):

        new_url = url
        if new_url is None: return None
        if "https://" in new_url:
            new_url = new_url.replace("https://","")

        elif "http://" in new_url:
            new_url = new_url.replace("http://","")

        elif "www." in new_url:
            new_url = new_url.replace("www.","")
        else:
            return ""

        return new_url

    @classmethod
    def extract_facebook_url(cls,url):

        if "story." in url.split("/")[1] or "photo." in url.split("/")[1]:
            url = url.split("/")[0] + "/" + url.split("fbid=")[1].split("&")[0].strip().split(" ")[0]
        elif "groups" == url.split("/")[1]:
            url =  url.split("/")[0] + "/" + url.split("/")[2].split(" ")[0]
        else:
            url = url.split("/")[0] + "/" + url.split("/")[1].split(" ")[0]

        return url

    @classmethod
    def extract_youtube_url(cls,url):

        if "channel" in url.split("/")[1] and not "watch?" in url.split("/")[1]:
            url = str("youtube.com" + "/" + "channel/" + url.split("/")[2].strip().split(" ")[0])
        elif "v=" in url:
            url = "youtube.com"
            #url = str("youtube.com"+"/"+"watch?v="+url.split("v=")[1].split("&")[0].strip().split(" ")[0])
        else:
            url = str("youtube.com" + "/" + url.split("/")[1].split(" ")[0])
        return url

    @classmethod
    def extract_twitter_url(cls,url):

        if "twitter.com/i/web" in url:
            url = "twitter.com"
        else:
            url = str("twitter.com" + "/" + url.split("/")[1].split(" ")[0])
        return url

    @classmethod
    def extract_instagram_url(cls,url):

        if "instagram.com/p/" in url:
            url = "instagram.com" + "/p/" + url.split("/")[2].split(" ")[0]
        else:
            url = "instagram.com" + "/" + url.split("/")[1].split(" ")[0]

        return url

    @classmethod
    def extract_reddit_url(cls,url):

        if "reddit.com/comments/" in url:
            url = "reddit.com" + "/" + url.split("/comments/")[1].split("/")[0]
        elif "reddit.com/r/" in url:
            url = "reddit.com" + "/r/" + url.split("/")[2].split(" ")[0]
        else:
            pass

        return url

    @classmethod
    def extract_domain(cls,url):

        try:
            domain = urlparse(url).netloc
        except:
            domain = url.split("/")[0]

        return domain

    @classmethod
    def extract_special_url(cls,url,full_url):

        if url is None: return None
        if "/" in url:
            if "facebook." in url:
                try:
                    special_url = cls.extract_facebook_url(url)
                except:
                    print ("ERROR")
                    print (url)
                    special_url = cls.extract_domain(full_url)
            elif "youtube." in url or "youtu.be" in url:
                try:
                    special_url = cls.extract_youtube_url(url)
                except:
                    print ("ERROR")
                    print (url)
                    special_url = cls.extract_domain(full_url)
            elif "twitter." in url:
                special_url = cls.extract_twitter_url(url)
            elif "instagram." in url:
                special_url = cls.extract_instagram_url(url)
            elif "reddit." in url:
                special_url = cls.extract_reddit_url(url)
            else:
                special_url = cls.extract_domain(full_url)
        else:
            special_url = cls.extract_domain(full_url)
        return special_url

    @classmethod
    @timeout_decorator.timeout(seconds=30)
    def get_url_from_scrape(cls,url):

        try:
            scrp = Scraper(settings={"change_user_agent":True})
            scrp.browser_init()
            try:
                scrp.browser.get(url)
                time.sleep(0.25)
            except TimeoutError as e:
                print ("Scraper timed out")
                scrp.browser.quit()
                return None, ""
            except Exception as e:
                print (e)
                scrp.browser.quit()
                return None, ""
            unpacked_url = scrp.browser.current_url
            html = scrp.browser.page_source
            print ("Url extracted using scrape : {0}".format(unpacked_url))
            scrp.browser.quit()
            return unpacked_url, html
        except Exception as e:
            print (e)
            return None, ""

    @classmethod
    def extract_title_and_raw_text(cls,html,unpacked_url):

        title = unpacked_url
        raw_text = ""
        try:
            titles = [t.text for t in BeautifulSoup(html,"html.parser").find_all("h1")]
            if len(list(titles)) > 0: title = titles[0]
        except Exception as e:
            print (e)
        try:
            raw_texts = [tex.text for tex in BeautifulSoup(html,"html.parser").find_all("p")]
            if len(raw_texts) > 0: raw_text = ' '.join(raw_texts)
        except Exception as e:
            print (e)
        return title, raw_text

    @classmethod
    def unpack_url(cls,url,force_unpack=True):

        if "http" not in url: url = "http://"+url
        if "https://www.facebook.com/" in url: return url, "", ""
        url = cls._recursive_trim(url)
        headers = {'User-Agent':random.choice(USER_AGENTS)}

        # Get initial response from remote server
        try:
            resp = requests.get(url, allow_redirects=True, timeout=5, headers=headers)
            status_code = resp.status_code
        except Exception as e:
            status_code = 404
            print (e)

        # Host might not allow your request. Check for status code 404 and initiate scrape.
        if status_code == 404:
            if force_unpack:
                unpacked_url, html = cls.get_url_from_scrape(url)
            else:
                print ("Simple unpack not possible for url : {}".format(url))
                return None, None, None

        # If request is not rejected, make extra check if unpack was succesful.
        # Check if one of common url-shorterners exist in url-string.
        else:
            unpacked_url = resp.url
            try:
                resp.encoding='utf-8'
                html = str(resp.text)
            except Exception as e:
                print (e)
                html = str(resp.text)
            for shortener in COMMON_SHORTERNERS:
                if str(shortener) in str(unpacked_url):
                    unpacked_url, html = cls.get_url_from_scrape(url)

        title, raw_text = cls.extract_title_and_raw_text(html,unpacked_url)
        return unpacked_url, title, raw_text

    @classmethod
    def extract_urls(cls,inp_text,with_unpack=True,force_unique=True):

        url_list = cls.get_url_list_from_text(inp_text)
        final_url_list = []
        unpacked_urls_parsed = set({})

        if len(url_list) == 0:
            return final_url_list

        for full_url in url_list:
            #print (full_url)
            if ".mp4" in str(full_url): continue
            if ".mp3" in str(full_url): continue
            if "." not in cls.remove_url_prefix(full_url): continue
            for prob in COMMON_PROBLEMS:
                if prob in full_url: continue
            if with_unpack:
                try:
                    unpacked_url, title, raw_text = cls.unpack_url(full_url)
                    special_url = cls.extract_special_url(cls.remove_url_prefix(unpacked_url),unpacked_url)
                except Exception as e:
                    print (e)
            else:
                url = cls.remove_url_prefix(full_url)
                unpacked_url = full_url
                title = full_url
                raw_text = ""
                special_url = cls.extract_special_url(url,full_url)
            if unpacked_url is None: continue
            if force_unique:
                if unpacked_url in unpacked_urls_parsed: continue
            unpacked_urls_parsed.add(unpacked_url)
            domain = cls.extract_domain(full_url)
            #if ".dk" in str(domain)[-3:]: continue
            final_url_list.append({"domain":special_url[:150],
            "org_url":full_url[:500],
            "link_url":full_url[:500],"display_url":unpacked_url,
            "title":title,"raw_text":raw_text})

        return final_url_list
