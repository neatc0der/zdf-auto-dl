#!/usr/bin/python2
import requests, re, os, sys, math, time, argparse
from ConfigParser import SafeConfigParser
from xml.dom.minidom import parseString
from pprint import pprint

class RingBuffer:
    def __init__(self, size_max):
        self.max = size_max
        self.data = []
        self.cur = 0
    def append(self, x):
        if len(self.data) == self.max:
            self.data[self.cur] = x
            self.cur = (self.cur + 1) % self.max
        else:
            self.data.append(x)
    def get(self):
        if len(self.data) == self.max:
            return self.data[self.cur]
        return self.data[-1]

def log(show, msg, suc, argdata = {}):
    if not argdata:
        global args
    else:
        args = argdata["args"]
    note = "INFO"
    if not suc:
        note = "ERROR"
    if not suc or args.verbose:
        print "[%s] %s: %s" % (note, show, msg)

def download_file(show, url, output, argdata = {}):
    if not argdata:
        global speed_limit
        global args
    else:
        speed_limit = argdata["speed_limit"]
        args = argdata["args"]
    resume_byte_pos = 0
    file_options = 'wb'
    if os.path.isfile(output):
        file_options = 'a+b'
        resume_byte_pos = os.path.getsize(output)
    resume_header = {'Range': 'bytes=%d-' % resume_byte_pos}
    r = requests.get(url, headers=resume_header, stream=True, verify=False)
    size = r.headers.get('content-length')
    if size is None:
        log(show, "file already downloaded", True)
        return
    size = resume_byte_pos + int(size)
    if size < resume_byte_pos:
        log(show, "existing file does not match in size", False)
        return
    size = math.ceil(float(size)/1024)
    ticks = RingBuffer(50)
    i = resume_byte_pos / 1024
    start = time.time()
    ticks.append(start)
    sleep_time = 0
    with open(output, file_options) as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk:
                f.write(chunk)
                f.flush()
                i += 1
                percent = float(i*100)/size
                speed = float(len(ticks.data))/(time.time() - ticks.get())
                ticks.append(time.time())
                waiting_time = 1024.0*(1.0/speed_limit - 1.0/speed)
                if args.progress:
                    print "\r%.1f %% - %.1f KB/s speed     " % (percent, speed),
                if waiting_time > sleep_time:
                    sleep_time += 0.000001
                if sleep_time > 0:
                    if waiting_time < sleep_time:
                        sleep_time -= 0.000001
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    else:
                        sleep_time = 0

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='ZDF Mediathek Auto Downloader')
    parser.add_argument("-v", "--verbose", help="print INFO messages", action="store_true")
    parser.add_argument("-p", "--progress", help="print download progress", action="store_true")
    args = parser.parse_args()

    if not os.path.isfile("zdf.ini"):
        log("config", "file is missing", False)
        sys.exit(1)

    parser = SafeConfigParser()
    parser.read('zdf.ini')
    try:
        speed_limit = int(parser.get("user", "speed"))
    except:
        speed_limit = 9999999999
    shows = parser.get("user", "shows").split(",")
    media_dir = parser.get("user", "media_dir")
    download_quality = parser.get("user", "quality")
    download_format = ".%s" % parser.get("user", "format")

    url = parser.get("zdf", "url")
    search_url = parser.get("zdf", "search")
    xml_url = parser.get("zdf", "xml")
    download_prefix = parser.get("zdf", "download_prefix")

    link_regex = re.compile('<a href=".*">', re.IGNORECASE)
    id_regex = re.compile('/(\d)+/')

    for show in shows:
        show = show.strip().lower()
        resp = requests.post(
            url + search_url, 
            params = {'sucheText': show},
        )

        find_string = ">%s<" % show
        parts = re.split(find_string, resp.text, flags=re.IGNORECASE)
        if len(parts) < 2:
            log(show, "not found in search engine", False)
            continue
        m = link_regex.findall(parts[0] + ">")
        if m:
            link = m[-1]
            link = url + link.split('"')[1]

            resp = requests.get(link)

            find_string = "%s.* vom " % show
            parts = re.split(find_string, resp.text, flags=re.IGNORECASE)
            try:
                date = parts[1].split("<")[0]
            except:
                log(show, "not found within the show", False)
                sys.exit(1)
                continue
            show_dir = os.path.join(media_dir, show)
            if not os.path.isdir(show_dir):
                os.makedirs(show_dir)
            output_file = os.path.join(show_dir, "%s-%s.%s" % (show, date, download_format))
            m = link_regex.findall(parts[0])
            if m:
                link = m[-1]
                link = url + link.split('"')[1]
                m = id_regex.search(link)
                media_id = link[m.start(0)+1:m.end(0)-1]

                link = url + xml_url % media_id
                resp = requests.get(link)

                xml_data = parseString(resp.text.encode("utf8"))

                download_link = ""
                for element in xml_data.getElementsByTagName("formitaet"):
                    quality = element.getElementsByTagName("quality")
                    if quality:
                        quality = quality[0].firstChild.nodeValue
                    if quality != download_quality:
                        continue
                    download = element.getElementsByTagName("url")
                    if download:
                        download = download[0].firstChild.nodeValue
                    if download.endswith(download_format) and download.startswith(download_prefix):
                        download_link = download
                        break

                if download_link:
                    log(show, "snatch successful", True)
                    try:
                        download_file(show, download_link, output_file)
                    except:
                        log(show, "download failed", False)
                    continue

        log(show, "not found", False)
