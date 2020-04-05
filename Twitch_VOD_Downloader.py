#Twitch VOD Downloader v1.0.1 https://github.com/EnterGin/Twitch-VOD-Downloader

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
        self.VOD_folder = 1 #0 - not create folder for processed VOD, 1 - create folder for processed VOD
        self.download_preview = 0 #0 - not download VOD preview, 1 - download VOD preview
        self.deleteVOD = 1 #0 - not delete downloaded VOD file, 1 - delete downloaded VOD file
        
        
        
        # vod configuration
        self.vod_id = ""
        self.quality = "best"
        
        # cmdstatecommand
        if self.cmdstate == 2:
            self.cmdstatecommand = "/min cmd.exe /k".split()
        elif self.cmdstate == 1:
            self.cmdstatecommand = "/min".split()
        else:
            self.cmdstatecommand = "".split()
        
        # start text
        print('Configuration:')
        print('Root path: ' + self.root_path)
        print('Ffmpeg path: ' + self.ffmpeg_path)
        self.timezone = pytz.timezone(self.timezoneName).localize(datetime.datetime.now()).tzinfo._utcoffset.seconds/60/60
        print('Timezone: ' + self.timezoneName + ' ' + '(' + str(self.timezone) + ')')
        if self.chatdownload == 1:
            print('Chat downloading Enabled')
        else:
            print('Chat downloading Disabled')
            
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
        
        VOD_year = int(created_at[:4])
        VOD_month = int(created_at[5:7])
        VOD_day = int(created_at[8:10])
        VOD_hour = int(created_at[11:13])
        VOD_minute = int(created_at[14:16])
        
        VOD_date = datetime.datetime(VOD_year, VOD_month, VOD_day, VOD_hour, VOD_minute)
        
        VOD_date_tz = VOD_date + timedelta(hours=self.timezone)        
        
        stream_folder = VOD_date_tz.strftime("%Y%m%d") + "_" + info["title"] + '_' + info["game"] + '_' + self.username
        stream_folder = "".join(x for x in stream_folder if x.isalnum() or not x in ["/","\\",":","?","*",'"',">","<","|"])
        
        stream_filename = VOD_date_tz.strftime("%Y%m%d_(%H-%M)") + "_" + self.vod_id + "_" + stream_folder[9:] + ".mp4"
        
        recorded_filename = os.path.join(self.downloaded_path, stream_filename)
        
        
        if self.VOD_folder == 1:
            processed_stream_path = os.path.join(self.processed_path, stream_folder)
        else:
            processed_stream_path = self.processed_path
            
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
                subprocess.call(['ffmpeg', '-y', '-i', recorded_filename, '-analyzeduration', '2147483647', '-probesize', '2147483647', '-c:v', 'copy', '-start_at_zero', '-copyts', '-bsf:a', 'aac_adtstoasc', os.path.join(processed_stream_path, stream_filename)])
                if self.deleteVOD == 1:
                    os.remove(recorded_filename)
            except Exception as e:
                print(e)
        else:
            print("Skip fixing. File not found.")

def main(argv):
    twitch_downloader = TwitchDownloader()
    usage_message = 'download.py -v <VOD id> -q <quality>'
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
