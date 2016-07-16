#!/usr/bin/env python
# GPL v 2.0 License
# Opsdisk LLC | opsdisk.com
from __future__ import print_function

import argparse
import google  # https://pypi.python.org/pypi/google
import os
import Queue
import random
import sys
import threading
import time
import urllib2


class Worker(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        while True:          
            # Grab URL off the queue
            url = mg.queue.get()
            try:
                request = urllib2.Request(url)

                # Assign a User-Agent
                # No -u
                if mg.userAgent == 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)':
                    request.add_header('User-Agent', 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)')
                # -u
                elif mg.userAgent is None:
                    request.add_header('User-Agent', random.choice(mg.randomUserAgents))   
                # -u "My custom user agent 2.0"
                else:
                    request.add_header('User-Agent', mg.userAgent)
                    
                response = urllib2.urlopen(request, timeout=mg.urlTimeout)
                
                # Download the file
                size = int(response.headers["Content-Length"])                
                print("[+] Downloading file - [" + str(size) + " bytes] " + url)                
                filename = str(url.split("/")[-1]) 
                with open(mg.saveDirectory + "/" + filename, 'wb') as fp:
                    fp.write(response.read())
                    fp.close() 

                mg.totalBytes += size

            except:
                print("[-] Timed out after " + str(mg.urlTimeout) + " seconds...can't reach url: " + url)
            
            mg.queue.task_done()


class Metagoofil:

    def __init__(self, domain, delay, saveLinks, urlTimeout, searchMax, downloadFileLimit, saveDirectory, numThreads, fileTypes, userAgent, downloadFiles):
        self.domain = domain
        self.delay = delay
        self.saveLinks = saveLinks
        self.urlTimeout = urlTimeout
        self.searchMax = searchMax
        self.downloadFileLimit = downloadFileLimit
        self.saveDirectory = saveDirectory

        # Create queue and specify the number of worker threads.
        self.queue = Queue.Queue() 
        self.numThreads = numThreads

        self.fileTypes = fileTypes
            
        self.userAgent = userAgent
        # Populate a list of random User-Agents
        if self.userAgent is None:
            with open('user_agents.txt') as fp:
                self.randomUserAgents = fp.readlines()
        
        self.downloadFiles = downloadFiles 
        self.totalBytes = 0

    def go(self):
        # Kickoff the threadpool.
        for i in range(self.numThreads):
            thread = Worker()
            thread.daemon = True
            thread.start()

        if "ALL" in self.fileTypes:
            from itertools import product
            from string import ascii_lowercase
            # Generate all three letter combinations
            self.fileTypes = [''.join(i) for i in product(ascii_lowercase, repeat=3)]

        for filetype in self.fileTypes:
            self.files = []  # Stores URLs with files, clear out for each filetype

            # Search for the files to download
            print("[*] Searching for " + str(self.searchMax) + " ." + filetype + " files and waiting " + str(self.delay) + " seconds between searches")
            query = "filetype:" + filetype + " site:" + self.domain
            for url in google.search(query, start=0, stop=self.searchMax, num=100, pause=self.delay, extra_params={'filter': '0'}):
                self.files.append(url)
            
            # Since google.search method retreives URLs in batches of 100, ensure the file list only contains the requested amount
            if len(self.files) > self.searchMax:
                self.files = self.files[:-(len(self.files) - self.searchMax)] 
                        
            # Download files if specified with -w switch
            if self.downloadFiles:
                self.download()
            
            # Otherwise, just display them
            else:
                print("[*] Results: " + str(len(self.files)) + " ." + filetype + " files found")
                for file in self.files:
                    print(file)
            
            # Save links to output to file
            if self.saveLinks:
                self.f = open('html_links_' + get_timestamp() + '.txt', 'a')
                for file in self.files:
                    self.f.write(file + "\n")
                self.f.close()
        
        if self.downloadFiles:
            print("[+] Total download: " + str(self.totalBytes) + " bytes / " + str(self.totalBytes / 1024) + " KB / " + str(self.totalBytes / (1024 * 1024)) + " MB")
                      
    def download(self):
        self.counter = 1
        for url in self.files:
            if self.counter <= self.downloadFileLimit:
                self.queue.put(url)
                self.counter += 1
        
        self.queue.join()


def get_timestamp():
    now = time.localtime()
    timestamp = time.strftime('%Y%m%d_%H%M%S', now)
    return timestamp


def csv_list(string):
    return string.split(',')                    


# http://stackoverflow.com/questions/3853722/python-argparse-how-to-insert-newline-in-the-help-text
class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()  
        # This is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Metagoofil - Search and Download Filetypes', formatter_class=SmartFormatter)
    parser.add_argument('-d', dest='domain', action='store', required=True, help='Domain to search')
    parser.add_argument('-e', dest='delay', action='store', type=float, default=7.0, help='Delay (in seconds) between searches.  If it\'s too small Google may block your IP, too big and your search may take a while.')
    parser.add_argument('-f', dest='saveLinks', action='store_true', default=False, help='Save the html links to html_links_<TIMESTAMP>.txt file')
    parser.add_argument('-i', dest='urlTimeout', action='store', type=int, default=5, help='Number of seconds to wait before timeout for unreachable/stale pages (default 5)')
    parser.add_argument('-l', dest='searchMax', action='store', type=int, default=100, help='Maximum results to search (default 100)')
    parser.add_argument('-n', dest='downloadFileLimit', default=100, action='store', type=int, help='Maximum number of files to download per filetype (default is 100)')    
    parser.add_argument('-o', dest='saveDirectory', action='store', default=os.getcwd(), help='Directory to save downloaded files (default is cwd, ".")')
    parser.add_argument('-r', dest='numThreads', action='store', type=int, default=8, help='Number of search threads (default is 8)')
    parser.add_argument('-t', dest='fileTypes', action='store', required=True, type=csv_list, help='Filetypes to download (pdf,doc,xls,ppt,odp,ods,docx,xlsx,pptx).  To search all 17,576 three-letter file extensions, type "ALL"')
    parser.add_argument('-u', dest='userAgent', nargs='?', default='Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)', help='R|User-Agent.\n'
                                                                                                                                               'no -u = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"\n'
                                                                                                                                               '-u = Randomize User-Agent\n'
                                                                                                                                               '-u "My custom user agent 2.0" = Your customized User-Agent')
    parser.add_argument('-w', dest='downloadFiles', action='store_true', default=False, help='Download the files, instead of just viewing search results')
    args = parser.parse_args()

    if not args.domain:
        print("[!] Specify a domain with -d")
        sys.exit()
    if not args.fileTypes:
        print("[!] Specify file types with -t")
        sys.exit()
    if (args.downloadFileLimit > 0) and (args.downloadFiles is False):
        print("[+] Adding -w for you")
        args.downloadFiles = True
    if args.saveDirectory:
        print("[*] Downloaded files will be saved here: " + args.saveDirectory)
        if not os.path.exists(args.saveDirectory):
            print("[+] Creating folder: " + args.saveDirectory)
            os.mkdir(args.saveDirectory)
    if args.delay < 0:
        print("[!] Delay must be greater than 0")
        sys.exit()
    if args.urlTimeout < 0:
        print("[!] URL timeout (-i) must be greater than 0")
        sys.exit()
    if args.numThreads < 0:
        print("[!] Number of threads (-n) must be greater than 0")
        sys.exit()
    
    #print(vars(args))
    mg = Metagoofil(**vars(args))
    mg.go()

    print("[+] Done!")