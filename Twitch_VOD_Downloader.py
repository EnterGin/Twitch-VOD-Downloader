#Twitch VOD Downloader v1.1.0 https://github.com/EnterGin/Twitch-VOD-Downloader

import requests
import os
import time
import json
import sys
import subprocess
import datetime
from datetime import timedelta
import getopt
import pytz

class TwitchDownloader:
    def __init__(self):
        # global configuration
        self.client_id = "kimne78kx3ncx6brgo4mv6wki5h1ko" # Don't change this
        self.ffmpeg_path = r"D:\\twitch" # path to ffmpeg.exe
        self.root_path = r"D:\\twitch" # path to recorded and processed streams
        self.timezoneName = 'Europe/Moscow' # name of timezone (list of timezones: https://stackoverflow.com/questions/13866926/is-there-a-list-of-pytz-timezones)
        self.chatdownload = 1 #0 - disable chat downloading, 1 - enable chat downloading
        self.cmdstate = 1 #0 - not minimazed cmd close after processing, 1 - minimazed cmd close after processing, 2 - minimazed cmd don't close after processing
        self.vod_folder = 1 #0 - not create folder for processed VOD, 1 - create folder for processed VOD
        self.short_folder = 0 #0 - only date in processed VOD folder, 1 - date, title, game and username in processed VOD folder
        self.download_preview = 0 #0 - not download VOD preview, 1 - download VOD preview
        self.deletevod = 1 #0 - not delete downloaded VOD file, 1 - delete downloaded VOD file
        
        # vod configuration
        self.vod_id = ""
        self.quality = "best"
        
    def VODinfo(self):    
        vodurl = "https://api.twitch.tv/kraken/videos/" + self.vod_id
        
        try:
            vod_info = requests.get(vodurl, headers = {"Accept" : 'application/vnd.twitchtv.v5+json', "Client-ID" : self.client_id}, timeout = 1)
            vod_info.raise_for_status()
            vod_infodic = json.loads(vod_info.text)
        except requests.exceptions.RequestException as e:
            if e.response != None:
                if e.response.reason == 'Bad Request':
                    vod_not_valid_window = "cmd.exe /c start".split()
                    subprocess.call(vod_not_valid_window + ['echo', 'VOD ID is not a valid ID.'])
                    sys.exit()
                elif e.response.reason == 'Not Found':
                    vod_not_found_window = "cmd.exe /c start".split()
                    subprocess.call(vod_not_found_window + ['echo', 'VOD not found.'])
                    sys.exit()    
                    
        self.username = vod_infodic["channel"]["name"]
        
        return vod_infodic
        
    def run(self):
        # cmdstatecommand
        if self.cmdstate == 2:
            self.cmdstatecommand = "/min cmd.exe /k".split()
        elif self.cmdstate == 1:
            self.cmdstatecommand = "/min".split()
        else:
            self.cmdstatecommand = "".split()
            
        # start text
        print('Twitch VOD Downloader v1.1.0')
        print('Configuration:')
        print('Root path: ' + self.root_path)
        print('Ffmpeg path: ' + self.ffmpeg_path)
        self.timezone = pytz.timezone(self.timezoneName).localize(datetime.datetime.now()).tzinfo._utcoffset.seconds/60/60
        print('Timezone: ' + self.timezoneName + ' ' + '(' + str(self.timezone) + ')')
        if self.chatdownload == 1:
            print('Chat downloading Enabled')
        else:
            print('Chat downloading Disabled')    
            
        self.VODinfo()
        
        # path to recorded stream
        self.downloaded_path = os.path.join(self.root_path, "downloaded", self.username)

        # path to finished video, errors removed
        self.processed_path = os.path.join(self.root_path, "processed", self.username)

        # create directory for recordedPath and processedPath if not exist
        if(os.path.isdir(self.downloaded_path) is False):
            os.makedirs(self.downloaded_path)
        if(os.path.isdir(self.processed_path) is False):
            os.makedirs(self.processed_path)

        self.download()  
        
        

    def download(self):
    
        info = self.VODinfo()
        
        created_at = info["created_at"]
        
        stream_title = str(info["title"])
        stream_title = "".join(x for x in stream_title if x.isalnum() or not x in ["/","\\",":","?","*",'"',">","<","|"])
        
        vod_year = int(created_at[:4])
        vod_month = int(created_at[5:7])
        vod_day = int(created_at[8:10])
        vod_hour = int(created_at[11:13])
        vod_minute = int(created_at[14:16])
        
        vod_date = datetime.datetime(vod_year, vod_month, vod_day, vod_hour, vod_minute)
        
        vod_date_tz = vod_date + timedelta(hours=self.timezone)        
        
        if self.short_folder == 1:
            stream_folder = vod_date_tz.strftime("%Y%m%d")
        else:
            stream_folder = vod_date_tz.strftime("%Y%m%d") + "_" + stream_title + '_' + str(info["game"]) + '_' + self.username
            stream_folder = "".join(x for x in stream_folder if x.isalnum() or not x in ["/","\\",":","?","*",'"',">","<","|"])
        
        stream_filename = vod_date_tz.strftime("%Y%m%d_(%H-%M)") + "_" + self.vod_id + "_" + stream_title + '_' + str(info["game"]) + '_' + self.username + ".mp4"
        stream_filename = "".join(x for x in stream_filename if x.isalnum() or not x in ["/","\\",":","?","*",'"',">","<","|"])
        
        recorded_filename = os.path.join(self.downloaded_path, stream_filename)
        
        if len(recorded_filename) >= 260:
            long_title_window = "cmd.exe /c start".split()
            difference = len(stream_title) - len(recorded_filename) + 250
            if difference < 0:
                subprocess.call(long_title_window + ['echo', 'Path to stream is too long. (Max path length is 259 symbols) Title cannot be cropped, please check root path.'])
                sys.exit()  
            else:
                stream_title = stream_title[:difference]
                stream_filename = vod_date_tz.strftime("%Y%m%d_(%H-%M)") + "_" + self.vod_id + "_" + stream_title + '_' + info["game"] + '_' + self.username + ".mp4"
                stream_filename = "".join(x for x in stream_filename if x.isalnum() or not x in ["/","\\",":","?","*",'"',">","<","|"])
                recorded_filename = os.path.join(self.downloaded_path, stream_filename)
            
        if self.vod_folder == 1:
            processed_stream_path = os.path.join(self.processed_path, stream_folder)
        else:
            processed_stream_path = self.processed_path
            
        processed_filename = os.path.join(processed_stream_path, stream_filename)
            
        if len(processed_filename) >= 260:
            long_title_window = "cmd.exe /c start".split()
            if self.short_folder == 1 or self.vod_folder == 0:
                difference = len(stream_title) - len(processed_filename) + 250
            else:
                difference = int((2*len(stream_title) - len(processed_filename) + 250)/2)
            if difference < 0:
                subprocess.call(long_title_window + ['echo', 'Path to stream is too long. (Max path length is 259 symbols) Title cannot be cropped, please check root path.'])
                sys.exit()  
            else:
                stream_title = stream_title[:difference]
                stream_filename = vod_date_tz.strftime("%Y%m%d_(%H-%M)") + "_" + self.vod_id + "_" + stream_title + '_' + info["game"] + '_' + self.username + ".mp4"
                stream_filename = "".join(x for x in stream_filename if x.isalnum() or not x in ["/","\\",":","?","*",'"',">","<","|"])
                if self.short_folder == 1:
                    stream_folder = vod_date_tz.strftime("%Y%m%d")
                else:
                    stream_folder = vod_date_tz.strftime("%Y%m%d") + "_" + stream_title + '_' + str(info["game"]) + '_' + self.username
                    stream_folder = "".join(x for x in stream_folder if x.isalnum() or not x in ["/","\\",":","?","*",'"',">","<","|"])
                if self.vod_folder == 1:
                    processed_stream_path = os.path.join(self.processed_path, stream_folder)
                else:
                    processed_stream_path = self.processed_path
                processed_filename = os.path.join(processed_stream_path, stream_filename)
                subprocess.call(long_title_window + ['echo', 'Path to stream is too long. (Max path length is 259 symbols) Title will be cropped, please check root path.'])
        
        if(os.path.isdir(processed_stream_path) is False):
            os.makedirs(processed_stream_path)
            
        subprocess.call(["streamlink", "twitch.tv/videos/" + self.vod_id, self.quality, "-o", recorded_filename])    
        
        if self.chatdownload == 1:
            subtitles_window = "cmd.exe /c start".split() + self.cmdstatecommand
            subprocess.call(subtitles_window + ["tcd", "-v", self.vod_id, "--timezone", self.timezoneName, "-f", "irc,ssa,json", "-o", processed_stream_path])
        if self.download_preview == 1:
            preview_url = info["preview"]["large"]
            preview_name = "PREVIEW_" + self.vod_id + ".jpg"
            preview_path = os.path.join(processed_stream_path, preview_name)
            img_data = requests.get(preview_url)
            open(preview_path, 'wb').write(img_data.content)
        
        print("Downloading stream is done. Fixing video file.")
        if(os.path.exists(recorded_filename) is True):
            try:
                os.chdir(self.ffmpeg_path)
                subprocess.call(['ffmpeg', '-y', '-i', recorded_filename, '-analyzeduration', '2147483647', '-probesize', '2147483647', '-c:v', 'copy', '-start_at_zero', '-copyts', '-bsf:a', 'aac_adtstoasc', processed_filename])
                if self.deletevod == 1:
                    os.remove(recorded_filename)
            except Exception as e:
                print(e)
        else:
            print("Skip fixing. File not found.")

def main(argv):
    twitch_downloader = TwitchDownloader()
    usage_message = 'Twitch_VOD_Downloader.py -v <VOD id> -q <quality>'
    try:
        opts, args = getopt.getopt(argv,"hv:q:",["vod_id=","quality="])
    except getopt.GetoptError:
        print (usage_message)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(usage_message)
            sys.exit()
        elif opt in ("-v", "--video"):
            twitch_downloader.vod_id = arg
        elif opt in ("-q", "--quality"):
            twitch_downloader.quality = arg
            
    twitch_downloader.run()

if __name__ == "__main__":
    main(sys.argv[1:])
