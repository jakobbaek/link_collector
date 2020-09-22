from datetime import datetime, timezone
import pytz
from langdetect import detect_langs

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def datetime_str_to_cet(data_dt,data_dt_format):
        parsed_dt = datetime.strptime(data_dt, data_dt_format).replace(tzinfo = pytz.utc)
        parsed_dt = parsed_dt.astimezone(tz=pytz.timezone('CET'))
        parsed_dt = parsed_dt.replace(tzinfo=None)
        return parsed_dt

def get_lang_and_conf(text,min_conf=.75):

    lang = "und"
    lang_conf = 0.0
    if len(text) > 0:
        try:
            suggestions = detect_langs(text)
        except Exception as e:
            suggestions = []
            #print (e)
        if len(suggestions) > 0:
            lang = str(suggestions[0]).split(":")[0]
            lang_conf = float(str(suggestions[0]).split(":")[1])
            if float(lang_conf) < .75:
                lang = "und"

    return {"lang":lang,"lang_conf":lang_conf}

def determine_platform_type(type_id):

    type = None
    if isinstance(type_id,int):
        if type_id == 1: type = "facebook"
        elif type_id == 2: type = "facebook"
        elif type_id == 3: type = "facebook"
        elif type_id == 5: type = "twitter"
        elif type_id == 8: type = "instagram"
        elif type_id == 11: type = "reddit"

    return type
