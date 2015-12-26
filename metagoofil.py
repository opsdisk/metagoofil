#!/usr/bin/env python
# GPL v 2.0 License
# Opsdisk LLC | opsdisk.com

import argparse
import google  # https://pypi.python.org/pypi/google
import os
import sys
import time
import urllib
import urllib2


class Metagoofil:

    def __init__(self, domain, fileTypes, searchMax, downloadFileLimit, maxDownloadSize, saveDirectory, downloadFiles, saveLinks, delay, urlTimeout):
        self.domain = domain
        self.fileTypes = fileTypes
        self.searchMax = searchMax
        self.downloadFileLimit = downloadFileLimit
        self.maxDownloadSize = maxDownloadSize
        self.saveDirectory = saveDirectory
        self.downloadFiles = downloadFiles
        self.saveLinks = saveLinks
        self.delay = delay
        self.totalBytes = 0
        self.urlTimeout = urlTimeout

    def go(self):
        if "ALL" in self.fileTypes:
            from itertools import product
            from string import ascii_lowercase
            # Generate all three letter combinations
            self.fileTypes = [''.join(i) for i in product(ascii_lowercase, repeat=3)]

        for filetype in self.fileTypes:
            # Search for the files to download
            print "[*] Searching for " + str(self.searchMax) + " ." + filetype + " files and waiting " + str(self.delay) + " seconds between searches"
            files = []
            query = "filetype:" + filetype + " site:" + self.domain
            for url in google.search(query, start=0, stop=self.searchMax, num=100, pause=self.delay):
                files.append(url)
            
            # Since google.search method retreives URLs in batches of 100, ensure the file list only contains the requested amount
            if len(files) > self.searchMax:
                files = files[:-(len(files) - self.searchMax)] 
                        
            # Download files if specified with -w argument
            if self.downloadFiles:
                self.download(files)
            
            # Otherwise, just display them
            else:
                print "[*] Results: " + str(len(files)) + " ." + filetype + " files found"
                for file in files:
                    print file
            
            # Save links to output to file
            if self.saveLinks:
                self.f = open('html_links_' + get_timestamp() + '.txt', 'a')
                for file in files:
                    self.f.write(file + "\n")
                self.f.close()
        
        if self.downloadFiles:
            print "[+] Total download: " + str(self.totalBytes) + " bytes / " + str(self.totalBytes / 1024) + " KB / " + str(self.totalBytes / (1024 * 1024)) + " MB"
                      
    def download(self, files):
        counter = 1
        for url in files:        
            if counter <= self.downloadFileLimit:
                try:
                    response = urllib2.urlopen(url, timeout=5)
                    # Determine if file is small enough to download
                    size = int(response.headers["Content-Length"])
                    if (size > self.maxDownloadSize):
                        print "[-] File is too large [" + str(size) + " bytes] to download " + url
                    else:
                        print "[+] Downloading file " + str(counter) + "/" + str(self.downloadFileLimit) + " - [" + str(size) + " bytes] " + url
                        filename = str(url.split("/")[-1]) 
                        urllib.urlretrieve(url, self.saveDirectory + "/" + filename)
                        self.totalBytes += size
                        counter += 1
                except:
                    print "[-] Timed out after " + str(self.urlTimeout) + " seconds...can't reach url: " + url            
                    
                               
def get_timestamp():
    now = time.localtime()
    timestamp = time.strftime('%Y%m%d_%H%M%S', now)
    return timestamp


def csv_list(string):
    return string.split(',')                    
   
   
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Metagoofil - Search and Download Filetypes')
    parser.add_argument('-d', dest='domain', action='store', required=True, help='Domain to search')
    parser.add_argument('-t', dest='fileTypes', action='store', required=True, type=csv_list, help='Filetypes to download (pdf,doc,xls,ppt,odp,ods,docx,xlsx,pptx).  To search all 17,576 three-letter file extensions, type "ALL"')
    parser.add_argument('-l', dest='searchMax', action='store', type=int, default=100, help='Maximum results to search (default 100)')
    parser.add_argument('-n', dest='downloadFileLimit', action='store', type=int, help='Maximum number of files to download per filetype')
    parser.add_argument('-m', dest='maxDownloadSize', action='store', type=int, default=5000000, help='Max filesize (in bytes) to download (default 5000000)')
    parser.add_argument('-o', dest='saveDirectory', action='store', default=os.getcwd(), help='Directory to save downloaded files (default is cwd, ".")')
    parser.add_argument('-w', dest='downloadFiles', action='store_true', default=False, help='Download the files, instead of just viewing search results')
    parser.add_argument('-f', dest='saveLinks', action='store_true', default=False, help='Save the html links to html_links_<TIMESTAMP>.txt file')
    parser.add_argument('-e', dest='delay', action='store', type=float, default=7.0, help='Delay (in seconds) between searches.  If it\'s too small Google may block your IP, too big and your search may take a while.')
    parser.add_argument('-i', dest='urlTimeout', action='store', type=int, default=5, help='Number of seconds to wait before timeout for unreachable/stale pages (default 5)')

    args = parser.parse_args()

    if not args.domain:
        print "[!] Specify a domain with -d"
        sys.exit()
    if not args.fileTypes:
        print "[!] Specify file types with -t"
        sys.exit()
    if (args.downloadFileLimit > 0) and (args.downloadFiles is False):
        print "[+] Adding -w for you"
        args.downloadFiles = True
    if args.saveDirectory:
        print "[*] Downloaded files will be saved here: " + args.saveDirectory
        if not os.path.exists(args.saveDirectory):
            print "[+] Creating folder: " + args.saveDirectory
            os.mkdir(args.saveDirectory)
    if args.delay < 0:
        print "[!] Delay must be greater than 0"
        sys.exit()
    if args.urlTimeout < 0:
        print "[!] URL timeout (-i) must be greater than 0"
        sys.exit()

    #print vars(args)
    mg = Metagoofil(**vars(args))
    mg.go()

    print "[+] Done!"
