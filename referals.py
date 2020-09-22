import pandas as pd
import pickle
from configparser import ConfigParser
import json
import os
import random
from operator import itemgetter
import sys
import helpers as hlp

from links import LinkUtils
from twitter import Twitter
from crowdtangle import Crowdtangle

class Collector:

    def __init__(self,url_list,title="test"):

        self.url_list = url_list
        self.url_loaded_data = None
        self.services = []
        self.url_tempsave = "_urls_temp/"
        self.running_export = "_exports/"
        self.title = title

        self.url_ids = {}
        self.url_reals = {}
        self.url_data = {}

        self.clean_urls = set([])
        self.max_url_id = 0

        self.url_referals = {}

        self.init_url_list()
        self.init_real_urls()

    def add_services(self,services=[]):

        for service in services:
            if not service in self.services:
                self.services.append(service)

    def export_referals(self):

        cols = set([])
        for refs in list(self.url_referals.values()):
             for ref in refs:
                 for col in ref.keys():
                     cols.add(col)
        cols.add("message_lang")
        cols.add("url_lang")
        cols = sorted(list(cols))
        export_data = []
        for refs in list(self.url_referals.values()):
            for ref in refs:
                ref["type_id"]=hlp.determine_platform_type(ref["type_id"])
                if "message" in ref:
                    ref["message_lang"]=hlp.get_lang_and_conf(ref["message"])["lang"]
                else:
                    ref["message_lang"]="und"
                ref["url_lang"]=hlp.get_lang_and_conf(self.url_data[ref["link_id"]]["raw_text"])["lang"]
                vals = []
                for col in cols:
                    if col in ref:
                        vals.append(ref[col])
                    else:
                        vals.append(0)
                export_data.append(vals)
        df = pd.DataFrame(export_data,columns=cols)
        df.to_excel("{0}{1}.xlsx".format(self.running_export,self.title))
        pickle.dump(self.url_referals,open(self.url_tempsave+"_url_data_refs.temp","wb"))

    def init_url_list(self):

        url_col = "url"
        if isinstance(self.url_list,list):
            pass
        elif isinstance(self.url_list,str):
            if "xlsx" in str(self.url_list):
                self.url_loaded_data = pd.read_excel(f'{self.url_list}', skip_blank_lines=False)
                if "Url" in set(list(self.url_loaded_data.columns)):
                    url_col = "Url"
                elif "url" in set(list(self.url_loaded_data.columns)):
                    url_col = "url"
                self.url_list = list(self.url_loaded_data[url_col])

    def init_real_urls(self):

        if not os.path.exists(self.url_tempsave):
            os.makedirs(self.url_tempsave)
        if not os.path.exists(self.running_export):
            os.makedirs(self.running_export)
        if os.path.exists(self.url_tempsave+"_url_ids_m.temp"):
            self.url_ids = pickle.load(open(self.url_tempsave+"_url_ids_m.temp","rb"))
        if os.path.exists(self.url_tempsave+"_url_real_m.temp"):
            self.url_reals = pickle.load(open(self.url_tempsave+"_url_real_m.temp","rb"))
        if os.path.exists(self.url_tempsave+"_url_data_m.temp"):
            self.url_data = pickle.load(open(self.url_tempsave+"_url_data_m.temp","rb"))
        if os.path.exists(self.url_tempsave+"_url_data_refs.temp"):
            self.url_referals = pickle.load(open(self.url_tempsave+"_url_data_refs.temp","rb"))

        if len(list(self.url_ids.values())) > 0:
            self.max_url_id=int(max(list(self.url_ids.values())))

        for url in self.url_list:
            org_url = url
            precleaned_url = LinkUtils.single_clean_url(url)

            if org_url in self.url_reals:
                if self.url_reals[org_url] in self.url_ids:
                    self.clean_urls.add(self.url_reals[org_url])
                else:
                    print ("ERROR - ID URL pair inconsistency!")
            else:
                print ("cleaning url - {0}".format(precleaned_url))
                url_data_packed = LinkUtils.extract_urls(precleaned_url)
                if url_data_packed:
                    url_data_packed = url_data_packed[0]
                    self.url_reals[org_url]=url_data_packed["display_url"]
                    if not url_data_packed["display_url"] in self.url_ids:
                        while self.max_url_id in set(list(self.url_ids.values())):
                            self.max_url_id+=1
                        self.url_ids[url_data_packed["display_url"]]=self.max_url_id
                        self.url_data[self.url_ids[url_data_packed["display_url"]]]=url_data_packed

                    self.clean_urls.add(self.url_reals[org_url])
                pickle.dump(self.url_ids,open(self.url_tempsave+"_url_ids_m.temp","wb"))
                pickle.dump(self.url_reals,open(self.url_tempsave+"_url_real_m.temp","wb"))
                pickle.dump(self.url_data,open(self.url_tempsave+"_url_data_m.temp","wb"))

    def get_referals(self,running_export=False,update=True):

        fname = "config"
        path = os.path.dirname(__file__)
        parser = ConfigParser()
        parser.read(path + f'/{fname}')

        tw = Twitter(api_keys=list(json.loads(str(parser["twitter"]["keys"]))))
        ct = Crowdtangle(api_tokens=list(json.loads(str(parser["crowdtangle"]["tokens"]))))

        print (len(self.url_referals))

        for url in list(self.clean_urls):
            #if not "information.dk" in url: continue
            if url not in self.url_referals:
                self.url_referals[url]=[]

            if url in self.url_referals and not update:
                pass
            else:
                if "crowdtangle" in self.services:
                    ct_referals = ct.get_url_referals(url,wait=random.randint(1,13))
                    self.url_referals[url].extend(ct_referals)

                if "twitter" in self.services:
                    tw_referals = tw.get_url_referals(url,include_retweets=True)
                    self.url_referals[url].extend(tw_referals)

                for dat in self.url_referals[url]:
                    if not isinstance(dat["link_id"],int):
                        dat["link_id"]=self.url_ids[dat["link_id"]]
                print ("{0} referals for - {1}".format(len(self.url_referals[url]),url))

            if running_export:
                if len(list(self.url_referals[url])) > 0:
                    self.export_referals()

        self.export_referals()
        return self.url_referals

class Populator:

    def __init__(self):

        pass
