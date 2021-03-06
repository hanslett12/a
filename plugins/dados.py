
#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function
from bs4 import BeautifulSoup
import progressbar
import requests
import sys
import config
import requests
import re
import json
import os
import html
import time
import datetime
from datetime import datetime
from urllib.parse import urlparse
from os.path import splitext
from urllib.request import urlretrieve
from urllib.request import urlopen
from shutil import copyfileobj
from tempfile import NamedTemporaryFile
import threading
import pprint
import traceback
import urllib.request
import amanobot
import amanobot.namedtuple
from tqdm import tqdm

try:
    import urllib.request
    python3 = True
except ImportError:
    import urllib2
    python3 = False
bot = config.bot
bot_username = config.bot_username
### XXX: hack to skip some stupid beautifulsoup warnings that I'll fix when refactoring
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')
TEMP_DOWNLOAD_DIRECTORY = os.environ.get("TMP_DOWNLOAD_DIRECTORY", "./downloads/")
def progress(current, total):
    print("Downloaded {} of {}\nCompleted {}".format(current, total, (current / total) * 100))
def make_progress_bar():
    return progressbar.ProgressBar(
        redirect_stdout=True,
        redirect_stderr=True,
        widgets=[
            progressbar.Percentage(),
            progressbar.Bar(),
            ' (',
            progressbar.AdaptiveTransferSpeed(),
            ' ',
            progressbar.ETA(),
            ') ',
        ])

def equivalent(data, nt):
    if type(data) is dict:
        keys = list(data.keys())

        # number of dictionary keys == number of non-None values in namedtuple?
        if len(keys) != len([f for f in nt._fields if getattr(nt, f) is not None]):
            return False

        # map `from` to `from_`
        fields = list([k+'_' if k in ['from'] else k for k in keys])

        return all(map(equivalent, [data[k] for k in keys], [getattr(nt, f) for f in fields]))
    elif type(data) is list:
        return all(map(equivalent, data, nt))
    else:
        return data==nt
def examine(result, type):
    try:
        print('Examining %s ......' % type)

        nt = type(**result)
        assert equivalent(result, nt), 'Not equivalent:::::::::::::::\n%s\n::::::::::::::::\n%s' % (result, nt)

        pprint.pprint(result)
        pprint.pprint(nt)
        print()
    except AssertionError:
        traceback.print_exc()
        answer = input('Do you want to continue? [y] ')
        if answer != 'y':
            exit(1)

def dados(msg):
    content_type, chat_type, chat_id, msg_date, msg_id = amanobot.glance(msg, long=True)
    if msg.get('text'):
        if msg['text'].startswith('/dl') or msg['text'].startswith('!dl'):
            input_str = msg['text'][3:]
            if input_str == '':
                bot.sendMessage(msg['chat']['id'], '*Use:* `/dl or !dl <url/link>`',
                                parse_mode='Markdown',
                                reply_to_message_id=msg['message_id'])
            else:
                app_name = input_str.split('/')[-1]
                sent = bot.sendMessage(msg['chat']['id'], "🔁 getting download link for {}".format(app_name), 'Markdown', reply_to_message_id=msg['message_id'])['message_id']
                if not os.path.isdir(TEMP_DOWNLOAD_DIRECTORY):
                    os.makedirs(TEMP_DOWNLOAD_DIRECTORY)
                site = "https://apkpure.com"
                url = "https://apkpure.com/search?q=%s" %(app_name)
                html = requests.get(url)
                parse = BeautifulSoup(html.text)
                for i in parse.find("p"):
                    a_url = i["href"]
                    app_url = site + a_url + "/download?from=details"
                    html2 = requests.get(app_url).text
                    parse2 = BeautifulSoup(html2, features="lxml")
                    links = []
                    for link in parse2.find_all('a', {'id': 'download_link'}):
                        links.append(link.get('href'))
                        downloadlink = link.get('href')
                        bot.editMessageText((msg['chat']['id'], sent), "⬇️ downloading from [⬇️ apkpure.com]({}) in progress...{}".format(downloadlink, upload_progress_string), 'Markdown', disable_web_page_preview=True)
                        #bot.deleteMessage(chat_id, sent)
                        required_file_name = TEMP_DOWNLOAD_DIRECTORY + "" + app_name + ".apk"
                        start = datetime.now()
                        chunk_size = 1024
                        r = requests.get(downloadlink, stream = True) 
                        with open(required_file_name,"wb") as apk:
                            for chunk in r.iter_content(chunk_size=chunk_size):
                                total_length = r.headers.get('content-length')
                                dl = 0
                                total_length = int(total_length)
                                if chunk:
                                    dl += len(chunk)
                                    done = int(100 * dl / total_length)
                                    apk.write(chunk)
                                    apk.flush()
                                    download_progress_string = "Downloading ... [%s of %s]" % (str(dl), str(total_length))
                                    upload_progress_string = "Uploading ... [%s of %s]" % (str(dl), str(total_length))
                            bot.editMessageText((msg['chat']['id'], sent), "⬆️ Uploading *{}* to Telegram \n\n {}".format(app_nam, upload_progress_string), 'Markdown')
                            time.sleep(5)
                            starts = datetime.now()
                            bot.sendChatAction(chat_id, 'upload_document')
                            tr = bot.sendDocument(chat_id, open(required_file_name, 'rb'), caption="@" + bot_username, parse_mode='Markdown')
                            examine(tr, amanobot.namedtuple.Message)
                            time.sleep(0.5)
                            ends = datetime.now()
                            mss = (ends - starts).seconds
                            os.remove(required_file_name)
                            bot.deleteMessage((msg['chat']['id'],sent))
                            
                            return True
def main(args):
    if len(args) != 2:
        sys.exit("use: %s com.blah.blah" %(args[0]))
    get_apk(args[1])

if __name__ == "__main__":
    main(args=sys.argv)
    
